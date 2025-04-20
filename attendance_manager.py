import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import os

# 페이지 설정
st.set_page_config(
    page_title="노쇼 현황 분석",
    page_icon="📊",
    layout="wide"
)

# 제목 및 설명
st.title("특강 노쇼 현황 분석")
st.markdown("이 앱은 특강 출석 데이터를 분석하여 노쇼 현황을 보여줍니다.")

# 파일 업로드 기능
uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

# CSV 파일 처리 함수
def process_csv_file(file):
    try:
        # 다양한 인코딩 시도
        encodings = ['utf-8', 'euc-kr', 'cp949']
        for encoding in encodings:
            try:
                df = pd.read_csv(file, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        # 필수 열 확인
        required_columns = ['번호', '등록일자', '이름', '학과', '전공', '학번', '학년', '핸드폰', '이메일', '특강명', '출석여부', '비고']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"필수 열이 누락되었습니다: {', '.join(missing_columns)}")
            return None
        
        # 출석여부가 비어있는 경우 노쇼로 처리
        df['출석여부'] = df['출석여부'].fillna('노쇼')
        
        # 전공이나 학년이 비어있는 경우 '미지정' 처리
        df['전공'] = df['전공'].fillna('미지정')
        df['학년'] = df['학년'].fillna('미지정')
        
        return df
    
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        return None

# 노쇼 데이터 분석 함수
def analyze_attendance_data(df):
    # 결측치 처리
    df = df.fillna({'비고': '', '전공': '미지정', '학년': '미지정'})
    
    # 출석여부가 비어있는 경우 노쇼로 처리
    df['출석여부'] = df['출석여부'].fillna('노쇼')
    df['출석여부'] = df['출석여부'].replace('', '노쇼')
    
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
    
    # 특강별 노쇼율 계산
    lecture_stats = df.groupby('특강명').agg(
        총학생수=('학번', 'count'),
        노쇼학생수=('출석여부', lambda x: (x == '노쇼').sum())
    ).reset_index()
    lecture_stats['노쇼율'] = (lecture_stats['노쇼학생수'] / lecture_stats['총학생수'] * 100).round(2)
    
    # 학과별 노쇼율 계산
    dept_stats = df.groupby('학과').agg(
        총학생수=('학번', 'count'),
        노쇼학생수=('출석여부', lambda x: (x == '노쇼').sum())
    ).reset_index()
    dept_stats['노쇼율'] = (dept_stats['노쇼학생수'] / dept_stats['총학생수'] * 100).round(2)
    
    # 전공별 노쇼율 계산
    major_stats = df.groupby('전공').agg(
        총학생수=('학번', 'count'),
        노쇼학생수=('출석여부', lambda x: (x == '노쇼').sum())
    ).reset_index()
    major_stats['노쇼율'] = (major_stats['노쇼학생수'] / major_stats['총학생수'] * 100).round(2)
    
    # 학년별 노쇼율 계산
    grade_stats = df.groupby('학년').agg(
        총학생수=('학번', 'count'),
        노쇼학생수=('출석여부', lambda x: (x == '노쇼').sum())
    ).reset_index()
    grade_stats['노쇼율'] = (grade_stats['노쇼학생수'] / grade_stats['총학생수'] * 100).round(2)
    
    # 노쇼 횟수별 학생 분류
    no_show_once = student_no_shows[student_no_shows['노쇼횟수'] == 1]
    no_show_twice = student_no_shows[student_no_shows['노쇼횟수'] == 2]
    no_show_multiple = student_no_shows[student_no_shows['노쇼횟수'] >= 3]
    
    return {
        'status_counts': status_counts,
        'lecture_status_distribution': lecture_status_distribution,
        'no_show_students': no_show_students,
        'student_no_shows': student_no_shows,
        'lecture_stats': lecture_stats,
        'dept_stats': dept_stats,
        'major_stats': major_stats,
        'grade_stats': grade_stats,
        'no_show_once': no_show_once,
        'no_show_twice': no_show_twice,
        'no_show_multiple': no_show_multiple
    }

# 데이터 다운로드 함수
def get_csv_download_link(df, filename):
    csv = df.to_csv(index=False).encode('utf-8-sig')
    return csv

# 메인 애플리케이션 로직
def main():       
    # 데이터 로드 부분
    if file_path:
        try:
            # 다양한 인코딩 시도
            encodings = ['utf-8', 'euc-kr', 'cp949']
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    st.success(f"파일이 성공적으로 로드되었습니다.")
                    break
                except UnicodeDecodeError:
                    continue
                
            if df is None:
                st.error("파일 인코딩을 확인할 수 없습니다.")
        except Exception as e:
            st.error(f"파일 로드 중 오류가 발생했습니다: {e}")
    
    # 데이터 처리 및 분석
    if df is not None:
        # 데이터 미리보기
        with st.expander("데이터 미리보기"):
            st.dataframe(df)
        
        # 필터 옵션
        st.sidebar.header("데이터 필터링")
        
        # 학과 필터 - NaN 값 처리 및 문자열로 변환 
        departments = df['학과'].fillna('미지정').astype(str).unique().tolist()
        all_departments = sorted(departments)
        selected_departments = st.sidebar.multiselect(
            "학과 선택",
            all_departments,
            default=all_departments
        )
        
        # 전공 필터 - NaN 값 처리 및 문자열로 변환
        majors = df['전공'].fillna('미지정').astype(str).unique().tolist()
        all_majors = sorted(majors)
        selected_majors = st.sidebar.multiselect(
            "전공 선택",
            all_majors,
            default=all_majors
        )
        
        # 학년 필터 - NaN 값 처리 및 문자열로 변환
        grades = df['학년'].fillna('미지정').astype(str).unique().tolist()
        all_grades = sorted(grades)
        selected_grades = st.sidebar.multiselect(
            "학년 선택",
            all_grades,
            default=all_grades
        )
        
        # 특강 필터 - NaN 값 처리 및 문자열로 변환
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
        
        # 데이터 분석
        analysis_results = analyze_attendance_data(filtered_df)
        
        # 결과 표시
        st.header("노쇼 현황 분석 결과")
        
        # 기본 통계
        total_records = len(filtered_df)  # 총 레코드 수 (한 학생이 여러 강의 등록 가능)
        total_students = len(filtered_df['학번'].unique())  # 고유 학생 수
        total_lectures = len(filtered_df['특강명'].unique())
        no_show_count = analysis_results['status_counts'].get('노쇼', 0)
        no_show_rate = no_show_count / total_records * 100 if total_records > 0 else 0
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("총 데이터 수", f"{total_records}건")
        col2.metric("고유 학생 수", f"{total_students}명")
        col3.metric("총 특강 수", f"{total_lectures}개")
        col4.metric("노쇼 건수", f"{no_show_count}건")
        col5.metric("노쇼율", f"{no_show_rate:.2f}%")
        
        # 특강별 출석 상태 분포
        st.subheader("특강별 출석 상태 분포")
        
        # 특강별 출석 상태 분포 계산
        lecture_status_counts = filtered_df.groupby(['특강명', '출석여부']).size().reset_index(name='인원수')
        
        # 특강 목록
        lectures = sorted(filtered_df['특강명'].unique())
        
        # 각 특강별로 출석 상태 분포 표시
        for lecture in lectures:
            st.write(f"**{lecture}**")
            lecture_data = lecture_status_counts[lecture_status_counts['특강명'] == lecture]
            if not lecture_data.empty:
                # 피벗 테이블로 변환하여 가독성 높이기
                pivot_df = lecture_data.pivot(index='특강명', columns='출석여부', values='인원수').fillna(0).astype(int)
                st.dataframe(pivot_df)
                
                # 해당 특강의 전체 학생 수
                total_students = lecture_data['인원수'].sum()
                st.write(f"전체 인원: {total_students}명")
                
                # 노쇼율 계산
                no_show_count = lecture_data[lecture_data['출석여부'] == '노쇼']['인원수'].sum() if '노쇼' in lecture_data['출석여부'].values else 0
                no_show_rate = (no_show_count / total_students * 100) if total_students > 0 else 0
                st.write(f"노쇼율: {no_show_rate:.2f}%")
                
                # 노쇼한 학생 정보 표시
                no_show_students_in_lecture = filtered_df[(filtered_df['특강명'] == lecture) & (filtered_df['출석여부'] == '노쇼')]
                if not no_show_students_in_lecture.empty:
                    st.write("**노쇼 학생 명단:**")
                    st.dataframe(
                        no_show_students_in_lecture[['번호', '학번', '이름', '학과', '전공', '학년', '핸드폰', '이메일', '등록일자', '비고']],
                        hide_index=True
                    )
                else:
                    st.write("노쇼 학생이 없습니다.")
            else:
                st.write("데이터가 없습니다.")
            st.markdown("---")
        
        # 노쇼 학생 관리
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
        
        # 전체 노쇼 학생 명단
        st.header("전체 노쇼 학생 명단")
        if not analysis_results['no_show_students'].empty:
            st.dataframe(
                analysis_results['no_show_students'][['번호', '학번', '이름', '학과', '전공', '학년', '핸드폰', '이메일', '특강명', '등록일자', '비고']],
                hide_index=True
            )
            
            # 노쇼 학생 데이터 다운로드
            no_show_csv = get_csv_download_link(
                analysis_results['no_show_students'],
                "no_show_students.csv"
            )
            st.download_button(
                "노쇼 학생 명단 다운로드",
                no_show_csv,
                "no_show_students.csv",
                "text/csv",
                key='download-no-show'
            )
        else:
            st.info("노쇼 학생이 없습니다.")
        
        # 분석 결과 다운로드
        st.header("분석 결과 다운로드")
        
        # 특강별 노쇼율 다운로드
        lecture_csv = get_csv_download_link(
            analysis_results['lecture_stats'],
            "lecture_stats.csv"
        )
        st.download_button(
            "특강별 노쇼 현황 다운로드",
            lecture_csv,
            "lecture_stats.csv",
            "text/csv",
            key='download-lecture'
        )
        
        # 학과별 노쇼율 다운로드
        dept_csv = get_csv_download_link(
            analysis_results['dept_stats'],
            "department_stats.csv"
        )
        st.download_button(
            "학과별 노쇼 현황 다운로드",
            dept_csv,
            "department_stats.csv",
            "text/csv",
            key='download-dept'
        )
        
        # 전공별 노쇼율 다운로드
        major_csv = get_csv_download_link(
            analysis_results['major_stats'],
            "major_stats.csv"
        )
        st.download_button(
            "전공별 노쇼 현황 다운로드",
            major_csv,
            "major_stats.csv",
            "text/csv",
            key='download-major'
        )
        
        # 학년별 노쇼율 다운로드
        grade_csv = get_csv_download_link(
            analysis_results['grade_stats'],
            "grade_stats.csv"
        )
        st.download_button(
            "학년별 노쇼 현황 다운로드",
            grade_csv,
            "grade_stats.csv",
            "text/csv",
            key='download-grade'
        )

if __name__ == "__main__":
    main()
