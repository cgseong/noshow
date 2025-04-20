import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import os

# 페이지 설정
def setup_page():
    st.set_page_config(
        page_title="노쇼 현황 분석",
        page_icon="📊",
        layout="wide"
    )
    st.title("특강 노쇼 현황 분석")
    st.markdown("이 앱은 특강 출석 데이터를 분석하여 노쇼 현황을 보여줍니다.")

# CSV 파일 목록 가져오기
def get_csv_files(folder_path="./"):
    try:
        csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        if not csv_files:
            st.error(f"{folder_path} 폴더에 CSV 파일이 없습니다.")
            return []
        return csv_files
    except FileNotFoundError:
        st.error(f"{folder_path} 폴더를 찾을 수 없습니다.")
        return []
    except Exception as e:
        st.error(f"파일 목록을 불러오는 중 오류가 발생했습니다: {e}")
        return []

# CSV 파일 처리 함수
def process_csv_file(file_path):
    try:
        # 다양한 인코딩 시도
        for encoding in ['utf-8', 'euc-kr', 'cp949']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        # DataFrame이 생성되었는지 확인
        if 'df' not in locals():
            st.error("파일을 읽을 수 없습니다. 인코딩 문제일 수 있습니다.")
            return None
        
        # 필수 열 확인
        required_columns = ['번호', '등록일자', '이름', '학과', '전공', '학번', '학년', '핸드폰', '이메일', '특강명', '출석여부', '비고']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"필수 열이 누락되었습니다: {', '.join(missing_columns)}")
            return None
        
        # 데이터 전처리
        df = preprocess_data(df)
        return df
    
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        return None

# 데이터 전처리 함수
def preprocess_data(df):
    # 결측치 처리
    df['출석여부'] = df['출석여부'].fillna('노쇼')
    df['출석여부'] = df['출석여부'].replace('', '노쇼')
    df['전공'] = df['전공'].fillna('미지정')
    df['학년'] = df['학년'].fillna('미지정')
    df['비고'] = df['비고'].fillna('')
    
    return df

# 필터 옵션 설정
def setup_filters(df):
    st.sidebar.header("데이터 필터링")
    
    # 학과 필터
    departments = df['학과'].fillna('미지정').astype(str).unique().tolist()
    all_departments = sorted(departments)
    selected_departments = st.sidebar.multiselect(
        "학과 선택",
        all_departments,
        default=all_departments
    )
    
    # 전공 필터
    majors = df['전공'].fillna('미지정').astype(str).unique().tolist()
    all_majors = sorted(majors)
    selected_majors = st.sidebar.multiselect(
        "전공 선택",
        all_majors,
        default=all_majors
    )
    
    # 학년 필터
    grades = df['학년'].fillna('미지정').astype(str).unique().tolist()
    all_grades = sorted(grades)
    selected_grades = st.sidebar.multiselect(
        "학년 선택",
        all_grades,
        default=all_grades
    )
    
    # 특강 필터
    lectures = df['특강명'].fillna('미지정').astype(str).unique().tolist()
    all_lectures = sorted(lectures)
    selected_lectures = st.sidebar.multiselect(
        "특강 선택",
        all_lectures,
        default=all_lectures
    )
    
    # 필터 적용
    filtered_df = df.copy()
    if selected_departments:
        filtered_df = filtered_df[filtered_df['학과'].isin(selected_departments)]
    if selected_majors:
        filtered_df = filtered_df[filtered_df['전공'].isin(selected_majors)]
    if selected_grades:
        filtered_df = filtered_df[filtered_df['학년'].isin(selected_grades)]
    if selected_lectures:
        filtered_df = filtered_df[filtered_df['특강명'].isin(selected_lectures)]
    
    return filtered_df

# 노쇼 데이터 분석 함수
def analyze_attendance_data(df):
    # 출석 상태별 카운트
    status_counts = df['출석여부'].value_counts().to_dict()
    
    # 특강별 출석상태 분포
    lecture_status_distribution = df.groupby(['특강명', '출석여부']).size().reset_index(name='인원수')
    
    # 노쇼 학생 식별
    no_show_students = df[df['출석여부'] == '노쇼']
    
    # 학생별 노쇼 횟수 계산
    student_no_shows = no_show_students.groupby('학번').size().reset_index(name='노쇼횟수')
    student_info = df[['학번', '이름', '학과', '전공', '학년']].drop_duplicates()
    student_no_shows = pd.merge(student_no_shows, student_info, on='학번', how='left')
    
    # 각종 통계 계산
    stats_dict = {}
    
    # 특강, 학과, 전공, 학년별 노쇼율 계산
    for category in ['특강명', '학과', '전공', '학년']:
        stats = df.groupby(category).agg(
            총학생수=('학번', 'count'),
            노쇼학생수=('출석여부', lambda x: (x == '노쇼').sum())
        ).reset_index()
        stats['노쇼율'] = (stats['노쇼학생수'] / stats['총학생수'] * 100).round(2)
        stats_dict[f"{category}_stats"] = stats
    
    # 노쇼 횟수별 학생 분류
    no_show_once = student_no_shows[student_no_shows['노쇼횟수'] == 1]
    no_show_twice = student_no_shows[student_no_shows['노쇼횟수'] == 2]
    no_show_multiple = student_no_shows[student_no_shows['노쇼횟수'] >= 3]
    
    return {
        'status_counts': status_counts,
        'lecture_status_distribution': lecture_status_distribution,
        'no_show_students': no_show_students,
        'student_no_shows': student_no_shows,
        'lecture_stats': stats_dict['특강명_stats'],
        'dept_stats': stats_dict['학과_stats'],
        'major_stats': stats_dict['전공_stats'],
        'grade_stats': stats_dict['학년_stats'],
        'no_show_once': no_show_once,
        'no_show_twice': no_show_twice,
        'no_show_multiple': no_show_multiple
    }

# 기본 통계 표시
def display_basic_stats(filtered_df, analysis_results):
    st.header("노쇼 현황 분석 결과")
    
    # 기본 통계
    total_records = len(filtered_df)
    total_students = len(filtered_df['학번'].unique())
    total_lectures = len(filtered_df['특강명'].unique())
    no_show_count = analysis_results['status_counts'].get('노쇼', 0)
    no_show_rate = no_show_count / total_records * 100 if total_records > 0 else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("총 데이터 수", f"{total_records}건")
    col2.metric("고유 학생 수", f"{total_students}명")
    col3.metric("총 특강 수", f"{total_lectures}개")
    col4.metric("노쇼 건수", f"{no_show_count}건")
    col5.metric("노쇼율", f"{no_show_rate:.2f}%")

# 특강별 출석 상태 분포 표시
def display_lecture_distribution(filtered_df, lecture_status_counts):
    st.subheader("특강별 출석 상태 분포")
    
    lectures = sorted(filtered_df['특강명'].unique())
    
    for lecture in lectures:
        st.write(f"**{lecture}**")
        lecture_data = lecture_status_counts[lecture_status_counts['특강명'] == lecture]
        
        if not lecture_data.empty:
            # 피벗 테이블로 변환
            try:
                pivot_df = lecture_data.pivot(index='특강명', columns='출석여부', values='인원수').fillna(0).astype(int)
                st.dataframe(pivot_df)
            except Exception as e:
                st.error(f"피벗 테이블 생성 중 오류: {e}")
                for status, count in zip(lecture_data['출석여부'], lecture_data['인원수']):
                    st.write(f"- {status}: {count}명")
            
            # 전체 인원 및 노쇼율
            total_students = lecture_data['인원수'].sum()
            st.write(f"전체 인원: {total_students}명")
            
            no_show_count = lecture_data[lecture_data['출석여부'] == '노쇼']['인원수'].sum() if '노쇼' in lecture_data['출석여부'].values else 0
            no_show_rate = (no_show_count / total_students * 100) if total_students > 0 else 0
            st.write(f"노쇼율: {no_show_rate:.2f}%")
            
            # 노쇼 학생 명단
            no_show_students = filtered_df[(filtered_df['특강명'] == lecture) & (filtered_df['출석여부'] == '노쇼')]
            if not no_show_students.empty:
                st.write("**노쇼 학생 명단:**")
                st.dataframe(
                    no_show_students[['번호', '학번', '이름', '학과', '전공', '학년', '핸드폰', '이메일', '등록일자', '비고']],
                    hide_index=True
                )
            else:
                st.write("노쇼 학생이 없습니다.")
        else:
            st.write("데이터가 없습니다.")
        st.markdown("---")

# 노쇼 학생 관리 정보 표시
def display_no_show_management(analysis_results):
    st.header("노쇼 학생 관리")
    
    # 3회 이상 노쇼 학생
    st.subheader("3회 이상 노쇼 학생 (최우선 관리)")
    if not analysis_results['no_show_multiple'].empty:
        st.dataframe(
            analysis_results['no_show_multiple'][['학번', '이름', '학과', '전공', '학년', '노쇼횟수']],
            hide_index=True
        )
        st.info("조치사항: 특강 참여 제한 및 상담 필요")
    else:
        st.info("해당하는 학생이 없습니다.")
    
    # 2회 노쇼 학생
    st.subheader("2회 노쇼 학생 (주의 관리)")
    if not analysis_results['no_show_twice'].empty:
        st.dataframe(
            analysis_results['no_show_twice'][['학번', '이름', '학과', '전공', '학년', '노쇼횟수']],
            hide_index=True
        )
        st.warning("조치사항: 경고장 발송 및 유선 연락")
    else:
        st.info("해당하는 학생이 없습니다.")
    
    # 1회 노쇼 학생
    st.subheader("1회 노쇼 학생 (일반 관리)")
    if not analysis_results['no_show_once'].empty:
        st.dataframe(
            analysis_results['no_show_once'][['학번', '이름', '학과', '전공', '학년', '노쇼횟수']],
            hide_index=True
        )
        st.success("조치사항: 이메일 알림")
    else:
        st.info("해당하는 학생이 없습니다.")

# 노쇼 학생 명단 표시
def display_no_show_students(analysis_results):
    st.header("전체 노쇼 학생 명단")
    if not analysis_results['no_show_students'].empty:
        st.dataframe(
            analysis_results['no_show_students'][['번호', '학번', '이름', '학과', '전공', '학년', '핸드폰', '이메일', '특강명', '등록일자', '비고']],
            hide_index=True
        )
        
        # 다운로드 버튼
        csv_data = get_csv_download_data(analysis_results['no_show_students'])
        st.download_button(
            "노쇼 학생 명단 다운로드",
            csv_data,
            "no_show_students.csv",
            "text/csv",
            key='download-no-show'
        )
    else:
        st.info("노쇼 학생이 없습니다.")

# 다운로드 기능 설정
def setup_downloads(analysis_results):
    st.header("분석 결과 다운로드")
    
    # 각 카테고리별 노쇼 현황 다운로드 버튼
    categories = {
        'lecture_stats': ('특강별', 'lecture_stats.csv'),
        'dept_stats': ('학과별', 'department_stats.csv'),
        'major_stats': ('전공별', 'major_stats.csv'),
        'grade_stats': ('학년별', 'grade_stats.csv')
    }
    
    for key, (label, filename) in categories.items():
        csv_data = get_csv_download_data(analysis_results[key])
        st.download_button(
            f"{label} 노쇼 현황 다운로드",
            csv_data,
            filename,
            "text/csv",
            key=f'download-{key}'
        )

# CSV 다운로드 데이터 생성
def get_csv_download_data(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# 메인 애플리케이션 로직
def main():
    # 페이지 설정
    setup_page()
    
    # CSV 파일 목록 가져오기
    folder_path = "./"
    csv_files = get_csv_files(folder_path)
    
    if not csv_files:
        st.warning("분석할 CSV 파일이 없습니다. 파일을 추가하고 다시 시도해주세요.")
        return
    
    # 파일 선택
    selected_file = st.selectbox(
        "분석할 CSV 파일 선택", 
        options=csv_files
    )
    
    file_path = os.path.join(folder_path, selected_file)
    st.success(f"선택된 파일: {selected_file}")
    
    # 파일 처리
    df = process_csv_file(file_path)
    
    if df is None:
        st.error("데이터를 로드할 수 없습니다.")
        return
    
    # 데이터 미리보기
    with st.expander("데이터 미리보기"):
        st.dataframe(df)
    
    # 필터 설정 및 적용
    filtered_df = setup_filters(df)
    
    # 데이터 분석
    analysis_results = analyze_attendance_data(filtered_df)
    
    # 기본 통계 표시
    display_basic_stats(filtered_df, analysis_results)
    
    # 특강별 출석 상태 분포
    display_lecture_distribution(filtered_df, analysis_results['lecture_status_distribution'])
    
    # 노쇼 학생 관리
    display_no_show_management(analysis_results)
    
    # 전체 노쇼 학생 명단
    display_no_show_students(analysis_results)
    
    # 다운로드 기능
    setup_downloads(analysis_results)

if __name__ == "__main__":
    main()
