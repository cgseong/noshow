import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import uuid

# 데이터 파일 경로 설정
DATA_DIR = "data"
DATA_FILE = f"{DATA_DIR}/lecture_data.csv"

# 데이터 디렉토리 생성
os.makedirs(DATA_DIR, exist_ok=True)

# 페이지 설정
st.set_page_config(page_title="특강 신청 노쇼 관리 시스템", layout="wide")

# 초기 데이터 구조
DEFAULT_DATA = {
    "students": [],  # 학생 정보
    "lectures": [],  # 강의 정보
    "registrations": [],  # 신청 내역
}

# 데이터 초기화 함수
def initialize_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame({"data": [json.dumps(DEFAULT_DATA)]})
        df.to_csv(DATA_FILE, index=False)

# 데이터 로드 함수
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        data = json.loads(df.iloc[0]['data'])
        return data
    initialize_data()
    return DEFAULT_DATA

# 데이터 저장 함수
def save_data(data):
    df = pd.DataFrame({"data": [json.dumps(data)]})
    df.to_csv(DATA_FILE, index=False)

# 테이블 데이터 추출 함수
def get_students():
    data = load_data()
    return pd.DataFrame(data["students"]) if data["students"] else pd.DataFrame()

def get_lectures():
    data = load_data()
    return pd.DataFrame(data["lectures"]) if data["lectures"] else pd.DataFrame()

def get_registrations():
    data = load_data()
    return pd.DataFrame(data["registrations"]) if data["registrations"] else pd.DataFrame()

# 테이블 데이터 업데이트 함수
def update_students(students_df):
    data = load_data()
    data["students"] = students_df.to_dict('records') if not students_df.empty else []
    save_data(data)

def update_lectures(lectures_df):
    data = load_data()
    data["lectures"] = lectures_df.to_dict('records') if not lectures_df.empty else []
    save_data(data)

def update_registrations(registrations_df):
    data = load_data()
    data["registrations"] = registrations_df.to_dict('records') if not registrations_df.empty else []
    save_data(data)

# 초기 데이터 로드
initialize_data()

# 메뉴 정의
st.sidebar.title("특강 신청 노쇼 관리 시스템")
menu = st.sidebar.radio(
    "메뉴 선택",
    ["대시보드", "학생 관리", "특강 관리", "신청 관리", "출석 체크", "노쇼 현황", "데이터 관리"]
)

# 대시보드
if menu == "대시보드":
    st.title("📊 특강 신청 노쇼 관리 시스템 대시보드")
    
    # 데이터 불러오기
    students_df = get_students()
    lectures_df = get_lectures()
    registrations_df = get_registrations()
    
    # 카드형 통계 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("등록된 학생 수", len(students_df) if not students_df.empty else 0)
    
    with col2:
        st.metric("등록된 특강 수", len(lectures_df) if not lectures_df.empty else 0)
    
    with col3:
        if not registrations_df.empty:
            total_registrations = len(registrations_df)
        else:
            total_registrations = 0
        st.metric("총 신청 건수", total_registrations)
    
    with col4:
        if not registrations_df.empty and 'noshow' in registrations_df.columns:
            noshow_count = len(registrations_df[registrations_df['noshow'] == True])
            if total_registrations > 0:
                noshow_rate = f"{(noshow_count / total_registrations * 100):.1f}%"
            else:
                noshow_rate = "0.0%"
        else:
            noshow_count = 0
            noshow_rate = "0.0%"
        st.metric("노쇼 건수 (비율)", f"{noshow_count} ({noshow_rate})")
    
    # 최근 신청 내역
    st.subheader("최근 신청 내역")
    if not registrations_df.empty:
        # 최신 날짜순으로 정렬
        recent_registrations = registrations_df.sort_values('registration_date', ascending=False).head(10)
        st.dataframe(recent_registrations)
    else:
        st.info("신청 내역이 없습니다.")
    
    # 다가오는 특강
    st.subheader("다가오는 특강")
    if not lectures_df.empty:
        today = datetime.now().strftime('%Y-%m-%d')
        upcoming_lectures = lectures_df[lectures_df['lecture_date'] >= today].sort_values('lecture_date').head(5)
        
        if not upcoming_lectures.empty:
            for i, lecture in upcoming_lectures.iterrows():
                st.markdown(f"**{lecture['lecture_name']}** - {lecture['lecture_date']}")
                if not registrations_df.empty:
                    lecture_registrations = registrations_df[registrations_df['lecture_name'] == lecture['lecture_name']]
                    st.markdown(f"신청인원: {len(lecture_registrations)}명")
        else:
            st.info("다가오는 특강이 없습니다.")
    else:
        st.info("등록된 특강이 없습니다.")

# 학생 관리
elif menu == "학생 관리":
    st.title("👨‍🎓 학생 관리")
    
    tab1, tab2, tab3 = st.tabs(["학생 목록", "학생 등록", "학생 검색"])
    
    # 학생 목록 탭
    with tab1:
        st.subheader("등록된 학생 목록")
        students_df = get_students()
        
        if not students_df.empty:
            st.dataframe(students_df)
        else:
            st.info("등록된 학생이 없습니다.")
    
    # 학생 등록 탭
    with tab2:
        st.subheader("새 학생 등록")
        
        with st.form("student_form"):
            student_id = st.text_input("학번")
            name = st.text_input("성명")
            department = st.text_input("학과")
            grade = st.text_input("학년")
            email = st.text_input("이메일")
            phone = st.text_input("전화번호")
            
            submitted = st.form_submit_button("학생 등록")
            
            if submitted:
                if not student_id or not name or not department or not grade:
                    st.error("필수 항목을 모두 입력해주세요.")
                else:
                    students_df = get_students()
                    
                    # 중복 학번 체크
                    is_duplicate = False
                    if not students_df.empty and 'student_id' in students_df.columns:
                        is_duplicate = student_id in students_df['student_id'].values
                    
                    if is_duplicate:
                        st.error("이미 등록된 학번입니다.")
                    else:
                        # 새 학생 정보
                        new_student = {
                            "student_id": student_id,
                            "name": name,
                            "department": department,
                            "grade": grade,
                            "email": email,
                            "phone": phone,
                            "noshow_count": 0,
                            "registration_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 데이터 업데이트
                        if students_df.empty:
                            students_df = pd.DataFrame([new_student])
                        else:
                            students_df = pd.concat([students_df, pd.DataFrame([new_student])], ignore_index=True)
                        
                        update_students(students_df)
                        st.success(f"학생 {name}(학번: {student_id})이(가) 등록되었습니다.")
    
    # 학생 검색 탭
    with tab3:
        st.subheader("학생 검색")
        search_option = st.selectbox("검색 기준", ["학번", "성명", "학과"])
        search_text = st.text_input("검색어")
        
        if st.button("검색"):
            if not search_text:
                st.warning("검색어를 입력하세요.")
            else:
                students_df = get_students()
                
                if not students_df.empty:
                    if search_option == "학번":
                        result = students_df[students_df['student_id'].str.contains(search_text)]
                    elif search_option == "성명":
                        result = students_df[students_df['name'].str.contains(search_text)]
                    else:  # "학과"
                        result = students_df[students_df['department'].str.contains(search_text)]
                    
                    if not result.empty:
                        st.dataframe(result)
                    else:
                        st.info("검색 결과가 없습니다.")
                else:
                    st.info("등록된 학생이 없습니다.")

# 특강 관리
elif menu == "특강 관리":
    st.title("📚 특강 관리")
    
    tab1, tab2 = st.tabs(["특강 목록", "특강 등록"])
    
    # 특강 목록 탭
    with tab1:
        st.subheader("등록된 특강 목록")
        lectures_df = get_lectures()
        
        if not lectures_df.empty:
            # 날짜 기준 필터링
            filter_option = st.radio("필터", ["모든 특강", "지난 특강", "다가오는 특강"])
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            if filter_option == "지난 특강":
                filtered_lectures = lectures_df[lectures_df['lecture_date'] < today]
            elif filter_option == "다가오는 특강":
                filtered_lectures = lectures_df[lectures_df['lecture_date'] >= today]
            else:
                filtered_lectures = lectures_df
            
            if not filtered_lectures.empty:
                # 신청 현황 추가
                registrations_df = get_registrations()
                if not registrations_df.empty:
                    lecture_stats = []
                    
                    for _, lecture in filtered_lectures.iterrows():
                        lecture_name = lecture['lecture_name']
                        lecture_regs = registrations_df[registrations_df['lecture_name'] == lecture_name]
                        
                        reg_count = len(lecture_regs)
                        noshow_count = len(lecture_regs[lecture_regs['noshow'] == True]) if 'noshow' in lecture_regs.columns else 0
                        
                        lecture_data = lecture.to_dict()
                        lecture_data['registration_count'] = reg_count
                        lecture_data['noshow_count'] = noshow_count
                        
                        lecture_stats.append(lecture_data)
                    
                    lecture_stats_df = pd.DataFrame(lecture_stats)
                    st.dataframe(lecture_stats_df)
                else:
                    st.dataframe(filtered_lectures)
            else:
                st.info(f"{filter_option}이 없습니다.")
        else:
            st.info("등록된 특강이 없습니다.")
    
    # 특강 등록 탭
    with tab2:
        st.subheader("새 특강 등록")
        
        with st.form("lecture_form"):
            lecture_name = st.text_input("특강명")
            lecture_date = st.date_input("특강 날짜")
            lecture_time = st.time_input("특강 시간")
            location = st.text_input("장소")
            capacity = st.number_input("정원", min_value=1, value=30)
            instructor = st.text_input("강사")
            description = st.text_area("설명")
            
            submitted = st.form_submit_button("특강 등록")
            
            if submitted:
                if not lecture_name or not location or not instructor:
                    st.error("필수 항목을 모두 입력해주세요.")
                else:
                    lectures_df = get_lectures()
                    
                    # 특강 중복 검사
                    is_duplicate = False
                    if not lectures_df.empty:
                        is_duplicate = (
                            (lectures_df['lecture_name'] == lecture_name) & 
                            (lectures_df['lecture_date'] == lecture_date.strftime('%Y-%m-%d'))
                        ).any()
                    
                    if is_duplicate:
                        st.error("동일한 날짜에 같은 이름의 특강이 이미 등록되어 있습니다.")
                    else:
                        # 새 특강 정보
                        new_lecture = {
                            "lecture_id": str(uuid.uuid4()),
                            "lecture_name": lecture_name,
                            "lecture_date": lecture_date.strftime('%Y-%m-%d'),
                            "lecture_time": lecture_time.strftime('%H:%M'),
                            "location": location,
                            "capacity": capacity,
                            "instructor": instructor,
                            "description": description,
                            "registration_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 데이터 업데이트
                        if lectures_df.empty:
                            lectures_df = pd.DataFrame([new_lecture])
                        else:
                            lectures_df = pd.concat([lectures_df, pd.DataFrame([new_lecture])], ignore_index=True)
                        
                        update_lectures(lectures_df)
                        st.success(f"특강 '{lecture_name}'이(가) 등록되었습니다.")

# 신청 관리
elif menu == "신청 관리":
    st.title("📝 신청 관리")
    
    tab1, tab2, tab3 = st.tabs(["신청 내역", "특강 신청", "신청 취소"])
    
    # 신청 내역 탭
    with tab1:
        st.subheader("특강 신청 내역")
        registrations_df = get_registrations()
        
        if not registrations_df.empty:
            # 필터링 옵션
            filter_options = st.multiselect(
                "필터링", 
                ["학번", "특강명", "노쇼 여부"]
            )
            
            filtered_df = registrations_df.copy()
            
            if "학번" in filter_options:
                student_id = st.text_input("학번")
                if student_id:
                    filtered_df = filtered_df[filtered_df['student_id'].str.contains(student_id)]
            
            if "특강명" in filter_options:
                lectures_df = get_lectures()
                if not lectures_df.empty:
                    lecture_names = lectures_df['lecture_name'].unique().tolist()
                    selected_lecture = st.selectbox("특강명", [""] + lecture_names)
                    if selected_lecture:
                        filtered_df = filtered_df[filtered_df['lecture_name'] == selected_lecture]
            
            if "노쇼 여부" in filter_options:
                noshow_status = st.radio("노쇼 여부", ["전체", "노쇼", "출석"])
                if noshow_status != "전체":
                    if 'noshow' in filtered_df.columns:
                        if noshow_status == "노쇼":
                            filtered_df = filtered_df[filtered_df['noshow'] == True]
                        else:  # "출석"
                            filtered_df = filtered_df[filtered_df['noshow'] == False]
            
            if not filtered_df.empty:
                st.dataframe(filtered_df)
            else:
                st.info("조건에 맞는 신청 내역이 없습니다.")
        else:
            st.info("신청 내역이 없습니다.")
    
    # 특강 신청 탭
    with tab2:
        st.subheader("특강 신청")
        
        # 학생 선택
        students_df = get_students()
        if not students_df.empty:
            student_options = students_df.apply(lambda row: f"{row['name']} ({row['student_id']})", axis=1).tolist()
            selected_student = st.selectbox("학생 선택", [""] + student_options)
            
            if selected_student:
                selected_id = selected_student.split("(")[1].split(")")[0]
                selected_name = selected_student.split(" (")[0]
                
                # 특강 선택
                lectures_df = get_lectures()
                if not lectures_df.empty:
                    # 날짜가 지나지 않은 특강만 필터링
                    today = datetime.now().strftime('%Y-%m-%d')
                    available_lectures = lectures_df[lectures_df['lecture_date'] >= today]
                    
                    if not available_lectures.empty:
                        lecture_options = available_lectures.apply(
                            lambda row: f"{row['lecture_name']} ({row['lecture_date']})", axis=1
                        ).tolist()
                        selected_lecture = st.selectbox("특강 선택", [""] + lecture_options)
                        
                        if selected_lecture:
                            lecture_name = selected_lecture.split(" (")[0]
                            lecture_date = selected_lecture.split("(")[1].split(")")[0]
                            
                            # 중복 신청 확인
                            registrations_df = get_registrations()
                            is_duplicate = False
                            
                            if not registrations_df.empty:
                                is_duplicate = (
                                    (registrations_df['student_id'] == selected_id) & 
                                    (registrations_df['lecture_name'] == lecture_name)
                                ).any()
                            
                            if is_duplicate:
                                st.error("이미 신청한 특강입니다.")
                            else:
                                if st.button("신청하기"):
                                    # 신청 정보 생성
                                    new_registration = {
                                        "registration_id": str(uuid.uuid4()),
                                        "student_id": selected_id,
                                        "student_name": selected_name,
                                        "lecture_name": lecture_name,
                                        "lecture_date": lecture_date,
                                        "registration_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        "attendance_checked": False,
                                        "noshow": False
                                    }
                                    
                                    # 데이터 업데이트
                                    if registrations_df.empty:
                                        registrations_df = pd.DataFrame([new_registration])
                                    else:
                                        registrations_df = pd.concat([registrations_df, pd.DataFrame([new_registration])], ignore_index=True)
                                    
                                    update_registrations(registrations_df)
                                    st.success(f"{selected_name} 학생의 '{lecture_name}' 특강 신청이 완료되었습니다.")
                    else:
                        st.info("신청 가능한 특강이 없습니다.")
                else:
                    st.info("등록된 특강이 없습니다.")
        else:
            st.info("등록된 학생이 없습니다. 먼저 학생을 등록해주세요.")
    
    # 신청 취소 탭
    with tab3:
        st.subheader("특강 신청 취소")
        
        # 학생 선택
        students_df = get_students()
        if not students_df.empty:
            student_options = students_df.apply(lambda row: f"{row['name']} ({row['student_id']})", axis=1).tolist()
            selected_student = st.selectbox("학생 선택", [""] + student_options, key="cancel_student")
            
            if selected_student:
                selected_id = selected_student.split("(")[1].split(")")[0]
                
                # 해당 학생의 신청 내역 확인
                registrations_df = get_registrations()
                if not registrations_df.empty:
                    student_registrations = registrations_df[registrations_df['student_id'] == selected_id]
                    
                    if not student_registrations.empty:
                        # 취소할 특강 선택
                        registration_options = student_registrations.apply(
                            lambda row: f"{row['lecture_name']} ({row['lecture_date']})", axis=1
                        ).tolist()
                        selected_registration = st.selectbox("취소할 특강 선택", [""] + registration_options)
                        
                        if selected_registration:
                            lecture_name = selected_registration.split(" (")[0]
                            
                            if st.button("신청 취소"):
                                # 해당 신청 내역 삭제
                                updated_registrations = registrations_df[
                                    ~((registrations_df['student_id'] == selected_id) & 
                                      (registrations_df['lecture_name'] == lecture_name))
                                ]
                                
                                update_registrations(updated_registrations)
                                st.success(f"'{lecture_name}' 특강 신청이 취소되었습니다.")
                    else:
                        st.info("해당 학생의 신청 내역이 없습니다.")
                else:
                    st.info("신청 내역이 없습니다.")
        else:
            st.info("등록된 학생이 없습니다.")

# 출석 체크
elif menu == "출석 체크":
    st.title("✅ 출석 체크")
    
    # 오늘 날짜의 특강 목록
    lectures_df = get_lectures()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not lectures_df.empty:
        today_lectures = lectures_df[lectures_df['lecture_date'] == today]
        
        if not today_lectures.empty:
            # 특강 선택
            lecture_options = today_lectures.apply(
                lambda row: f"{row['lecture_name']} ({row['lecture_time']})", axis=1
            ).tolist()
            selected_lecture = st.selectbox("오늘의 특강 선택", [""] + lecture_options)
            
            if selected_lecture:
                lecture_name = selected_lecture.split(" (")[0]
                
                # 신청자 목록 불러오기
                registrations_df = get_registrations()
                
                if not registrations_df.empty:
                    lecture_registrations = registrations_df[registrations_df['lecture_name'] == lecture_name]
                    
                    if not lecture_registrations.empty:
                        st.subheader(f"{lecture_name} 출석 체크")
                        st.write(f"총 {len(lecture_registrations)}명의 신청자가 있습니다.")
                        
                        # 출석체크 표시
                        for i, reg in lecture_registrations.iterrows():
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                st.write(f"**{reg['student_name']}** (학번: {reg['student_id']})")
                            
                            with col2:
                                if st.button("출석", key=f"attend_{reg['student_id']}"):
                                    # 출석 체크 (노쇼=False)
                                    registrations_df.loc[
                                        (registrations_df['student_id'] == reg['student_id']) & 
                                        (registrations_df['lecture_name'] == lecture_name),
                                        ['attendance_checked', 'noshow']
                                    ] = [True, False]
                                    
                                    update_registrations(registrations_df)
                                    st.success(f"{reg['student_name']} 학생 출석 처리되었습니다.")
                                    st.rerun()
                                
                                if st.button("노쇼", key=f"noshow_{reg['student_id']}"):
                                    # 노쇼 체크 (노쇼=True)
                                    registrations_df.loc[
                                        (registrations_df['student_id'] == reg['student_id']) & 
                                        (registrations_df['lecture_name'] == lecture_name),
                                        ['attendance_checked', 'noshow']
                                    ] = [True, True]
                                    
                                    # 학생의 노쇼 카운트 증가
                                    students_df = get_students()
                                    if not students_df.empty:
                                        students_df.loc[
                                            students_df['student_id'] == reg['student_id'],
                                            'noshow_count'
                                        ] += 1
                                        
                                        update_students(students_df)
                                    
                                    update_registrations(registrations_df)
                                    st.error(f"{reg['student_name']} 학생 노쇼 처리되었습니다.")
                                    st.rerun()
                            
                            # 이미 체크된 경우 상태 표시
                            if 'attendance_checked' in reg and reg['attendance_checked']:
                                if 'noshow' in reg and reg['noshow']:
                                    st.error("노쇼")
                                else:
                                    st.success("출석 완료")
                            
                            st.markdown("---")
                    else:
                        st.info("해당 특강에 신청한 학생이 없습니다.")
                else:
                    st.info("신청 내역이 없습니다.")
        else:
            st.info("오늘 예정된 특강이 없습니다.")
    else:
        st.info("등록된 특강이 없습니다.")

# 노쇼 현황
elif menu == "노쇼 현황":
    st.title("⚠️ 노쇼 현황")
    
    tab1, tab2 = st.tabs(["노쇼 학생 목록", "노쇼 통계"])
    
    # 노쇼 학생 목록 탭
    with tab1:
        st.subheader("노쇼 학생 목록")
        
        registrations_df = get_registrations()
        
        if not registrations_df.empty and 'noshow' in registrations_df.columns:
            noshow_registrations = registrations_df[registrations_df['noshow'] == True]
            
            if not noshow_registrations.empty:
                st.dataframe(noshow_registrations)
                
                # 노쇼 학생 상세 정보
                st.subheader("노쇼 학생 상세 정보")
                
                students_df = get_students()
                if not students_df.empty:
                    # 노쇼 횟수별로 학생 정보 집계
                    student_noshows = noshow_registrations.groupby('student_id').size().reset_index()
                    student_noshows.columns = ['student_id', 'noshow_count']
                    
                    # 학생 정보와 병합
                    student_details = students_df.merge(student_noshows, on='student_id', how='inner')
                    
                    # 노쇼 횟수 내림차순 정렬
                    student_details = student_details.sort_values('noshow_count', ascending=False)
                    
                    st.dataframe(student_details)
            else:
                st.info("노쇼 기록이 없습니다.")
        else:
            st.info("신청 내역이 없거나 노쇼 데이터가 없습니다.")
    
    # 노쇼 통계 탭
    with tab2:
        st.subheader("노쇼 통계")
        
        registrations_df = get_registrations()
        
        if not registrations_df.empty and 'noshow' in registrations_df.columns:
            # 전체 노쇼율
            total_regs = len(registrations_df)
            noshow_regs = len(registrations_df[registrations_df['noshow'] == True])
            # 전체 노쇼율
            total_regs = len(registrations_df)
            noshow_regs = len(registrations_df[registrations_df['noshow'] == True])
            
            if total_regs > 0:
                noshow_rate = noshow_regs / total_regs * 100
            else:
                noshow_rate = 0
            
            st.metric("전체 노쇼율", f"{noshow_rate:.1f}%")
            
            # 특강별 노쇼율
            st.subheader("특강별 노쇼율")
            
            lecture_stats = []
            for lecture_name in registrations_df['lecture_name'].unique():
                lecture_regs = registrations_df[registrations_df['lecture_name'] == lecture_name]
                lecture_total = len(lecture_regs)
                lecture_noshows = len(lecture_regs[lecture_regs['noshow'] == True])
                
                if lecture_total > 0:
                    lecture_noshow_rate = lecture_noshows / lecture_total * 100
                else:
                    lecture_noshow_rate = 0
                
                lecture_stats.append({
                    '특강명': lecture_name,
                    '전체 신청자': lecture_total,
                    '노쇼 인원': lecture_noshows,
                    '노쇼율(%)': round(lecture_noshow_rate, 1)
                })
            
            if lecture_stats:
                lecture_stats_df = pd.DataFrame(lecture_stats)
                lecture_stats_df = lecture_stats_df.sort_values('노쇼율(%)', ascending=False)
                
                st.dataframe(lecture_stats_df)
                
                # 특강별 노쇼율 차트
                st.subheader("특강별 노쇼율 차트")
                chart_data = lecture_stats_df.set_index('특강명')['노쇼율(%)']
                st.bar_chart(chart_data)
            
            # 학과별 노쇼율
            st.subheader("학과별 노쇼율")
            
            students_df = get_students()
            if not students_df.empty and 'department' in students_df.columns:
                # 학생 정보에 학과 정보 가져오기
                merged_data = registrations_df.merge(
                    students_df[['student_id', 'department']], 
                    on='student_id',
                    how='left'
                )
                
                dept_stats = []
                for dept in merged_data['department'].unique():
                    if pd.isna(dept):
                        continue
                        
                    dept_regs = merged_data[merged_data['department'] == dept]
                    dept_total = len(dept_regs)
                    dept_noshows = len(dept_regs[dept_regs['noshow'] == True])
                    
                    if dept_total > 0:
                        dept_noshow_rate = dept_noshows / dept_total * 100
                    else:
                        dept_noshow_rate = 0
                    
                    dept_stats.append({
                        '학과': dept,
                        '전체 신청자': dept_total,
                        '노쇼 인원': dept_noshows,
                        '노쇼율(%)': round(dept_noshow_rate, 1)
                    })
                
                if dept_stats:
                    dept_stats_df = pd.DataFrame(dept_stats)
                    dept_stats_df = dept_stats_df.sort_values('노쇼율(%)', ascending=False)
                    
                    st.dataframe(dept_stats_df)
                    
                    # 학과별 노쇼율 차트
                    st.subheader("학과별 노쇼율 차트")
                    chart_data = dept_stats_df.set_index('학과')['노쇼율(%)']
                    st.bar_chart(chart_data)
        else:
            st.info("신청 내역이 없거나 노쇼 데이터가 없습니다.")

# 데이터 관리
elif menu == "데이터 관리":
    st.title("🗄️ 데이터 관리")
    
    tab1, tab2, tab3 = st.tabs(["데이터 내보내기", "데이터 백업", "데이터 초기화"])
    
    # 데이터 내보내기 탭
    with tab1:
        st.subheader("데이터 내보내기 (CSV)")
        
        export_option = st.selectbox(
            "내보낼 데이터 선택",
            ["학생 정보", "특강 정보", "신청 내역", "노쇼 현황"]
        )
        
        if st.button("CSV 파일 생성"):
            if export_option == "학생 정보":
                df = get_students()
                filename = "students.csv"
            elif export_option == "특강 정보":
                df = get_lectures()
                filename = "lectures.csv"
            elif export_option == "신청 내역":
                df = get_registrations()
                filename = "registrations.csv"
            elif export_option == "노쇼 현황":
                df = get_registrations()
                if not df.empty and 'noshow' in df.columns:
                    df = df[df['noshow'] == True]
                filename = "noshows.csv"
            
            if df is not None and not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"{export_option} 다운로드",
                    data=csv,
                    file_name=filename,
                    mime='text/csv',
                )
            else:
                st.warning("내보낼 데이터가 없습니다.")
    
    # 데이터 백업 탭
    with tab2:
        st.subheader("데이터 백업 및 복원")
        
        if st.button("데이터 백업"):
            data = load_data()
            if data:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = f"backup_{timestamp}.json"
                
                json_data = json.dumps(data, indent=4)
                st.download_button(
                    label="백업 파일 다운로드",
                    data=json_data,
                    file_name=backup_file,
                    mime='application/json',
                )
                st.success("데이터 백업이 생성되었습니다.")
            else:
                st.warning("백업할 데이터가 없습니다.")
        
        st.subheader("백업 데이터 복원")
        uploaded_file = st.file_uploader("백업 파일 선택 (.json)", type=["json"])
        
        if uploaded_file is not None:
            if st.button("데이터 복원"):
                try:
                    backup_data = json.loads(uploaded_file.getvalue())
                    save_data(backup_data)
                    st.success("데이터가 성공적으로 복원되었습니다.")
                except Exception as e:
                    st.error(f"데이터 복원 중 오류가 발생했습니다: {str(e)}")
    
    # 데이터 초기화 탭
    with tab3:
        st.subheader("데이터 초기화")
        st.warning("이 작업은 되돌릴 수 없습니다. 데이터 백업을 먼저 수행하는 것을 권장합니다.")
        
        reset_option = st.selectbox(
            "초기화할 데이터 선택",
            ["전체 데이터", "학생 데이터", "특강 데이터", "신청 내역"]
        )
        
        confirm = st.checkbox("초기화를 진행하겠습니다. 이 작업은 되돌릴 수 없습니다.")
        
        if confirm and st.button("데이터 초기화 실행"):
            data = load_data()
            
            if data:
                if reset_option == "전체 데이터":
                    save_data(DEFAULT_DATA)
                    st.success("모든 데이터가 초기화되었습니다.")
                elif reset_option == "학생 데이터":
                    data["students"] = []
                    save_data(data)
                    st.success("학생 데이터가 초기화되었습니다.")
                elif reset_option == "특강 데이터":
                    data["lectures"] = []
                    save_data(data)
                    st.success("특강 데이터가 초기화되었습니다.")
                elif reset_option == "신청 내역":
                    data["registrations"] = []
                    save_data(data)
                    st.success("신청 내역이 초기화되었습니다.")
            else:
                st.warning("초기화할 데이터가 없습니다.")

# 푸터 정보
st.sidebar.markdown("---")
st.sidebar.info("© 2025 특강 신청 노쇼 관리 시스템")
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import uuid

# 데이터 파일 경로 설정
DATA_DIR = "data"
DATA_FILE = f"{DATA_DIR}/lecture_data.csv"

# 데이터 디렉토리 생성
os.makedirs(DATA_DIR, exist_ok=True)

# 페이지 설정
st.set_page_config(page_title="특강 신청 노쇼 관리 시스템", layout="wide")

# 초기 데이터 구조
DEFAULT_DATA = {
    "students": [],  # 학생 정보
    "lectures": [],  # 강의 정보
    "registrations": [],  # 신청 내역
}

# 데이터 초기화 함수
def initialize_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame({"data": [json.dumps(DEFAULT_DATA)]})
        df.to_csv(DATA_FILE, index=False)

# 데이터 로드 함수
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        data = json.loads(df.iloc[0]['data'])
        return data
    initialize_data()
    return DEFAULT_DATA

# 데이터 저장 함수
def save_data(data):
    df = pd.DataFrame({"data": [json.dumps(data)]})
    df.to_csv(DATA_FILE, index=False)

# 테이블 데이터 추출 함수
def get_students():
    data = load_data()
    return pd.DataFrame(data["students"]) if data["students"] else pd.DataFrame()

def get_lectures():
    data = load_data()
    return pd.DataFrame(data["lectures"]) if data["lectures"] else pd.DataFrame()

def get_registrations():
    data = load_data()
    return pd.DataFrame(data["registrations"]) if data["registrations"] else pd.DataFrame()

# 테이블 데이터 업데이트 함수
def update_students(students_df):
    data = load_data()
    data["students"] = students_df.to_dict('records') if not students_df.empty else []
    save_data(data)

def update_lectures(lectures_df):
    data = load_data()
    data["lectures"] = lectures_df.to_dict('records') if not lectures_df.empty else []
    save_data(data)

def update_registrations(registrations_df):
    data = load_data()
    data["registrations"] = registrations_df.to_dict('records') if not registrations_df.empty else []
    save_data(data)

# 초기 데이터 로드
initialize_data()

# 메뉴 정의
st.sidebar.title("특강 신청 노쇼 관리 시스템")
menu = st.sidebar.radio(
    "메뉴 선택",
    ["대시보드", "학생 관리", "특강 관리", "신청 관리", "출석 체크", "노쇼 현황", "데이터 관리"]
)

# 대시보드
if menu == "대시보드":
    st.title("📊 특강 신청 노쇼 관리 시스템 대시보드")
    
    # 데이터 불러오기
    students_df = get_students()
    lectures_df = get_lectures()
    registrations_df = get_registrations()
    
    # 카드형 통계 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("등록된 학생 수", len(students_df) if not students_df.empty else 0)
    
    with col2:
        st.metric("등록된 특강 수", len(lectures_df) if not lectures_df.empty else 0)
    
    with col3:
        if not registrations_df.empty:
            total_registrations = len(registrations_df)
        else:
            total_registrations = 0
        st.metric("총 신청 건수", total_registrations)
    
    with col4:
        if not registrations_df.empty and 'noshow' in registrations_df.columns:
            noshow_count = len(registrations_df[registrations_df['noshow'] == True])
            if total_registrations > 0:
                noshow_rate = f"{(noshow_count / total_registrations * 100):.1f}%"
            else:
                noshow_rate = "0.0%"
        else:
            noshow_count = 0
            noshow_rate = "0.0%"
        st.metric("노쇼 건수 (비율)", f"{noshow_count} ({noshow_rate})")
    
    # 최근 신청 내역
    st.subheader("최근 신청 내역")
    if not registrations_df.empty:
        # 최신 날짜순으로 정렬
        recent_registrations = registrations_df.sort_values('registration_date', ascending=False).head(10)
        st.dataframe(recent_registrations)
    else:
        st.info("신청 내역이 없습니다.")
    
    # 다가오는 특강
    st.subheader("다가오는 특강")
    if not lectures_df.empty:
        today = datetime.now().strftime('%Y-%m-%d')
        upcoming_lectures = lectures_df[lectures_df['lecture_date'] >= today].sort_values('lecture_date').head(5)
        
        if not upcoming_lectures.empty:
            for i, lecture in upcoming_lectures.iterrows():
                st.markdown(f"**{lecture['lecture_name']}** - {lecture['lecture_date']}")
                if not registrations_df.empty:
                    lecture_registrations = registrations_df[registrations_df['lecture_name'] == lecture['lecture_name']]
                    st.markdown(f"신청인원: {len(lecture_registrations)}명")
        else:
            st.info("다가오는 특강이 없습니다.")
    else:
        st.info("등록된 특강이 없습니다.")

# 학생 관리
elif menu == "학생 관리":
    st.title("👨‍🎓 학생 관리")
    
    tab1, tab2, tab3 = st.tabs(["학생 목록", "학생 등록", "학생 검색"])
    
    # 학생 목록 탭
    with tab1:
        st.subheader("등록된 학생 목록")
        students_df = get_students()
        
        if not students_df.empty:
            st.dataframe(students_df)
        else:
            st.info("등록된 학생이 없습니다.")
    
    # 학생 등록 탭
    with tab2:
        st.subheader("새 학생 등록")
        
        with st.form("student_form"):
            student_id = st.text_input("학번")
            name = st.text_input("성명")
            department = st.text_input("학과")
            grade = st.text_input("학년")
            email = st.text_input("이메일")
            phone = st.text_input("전화번호")
            
            submitted = st.form_submit_button("학생 등록")
            
            if submitted:
                if not student_id or not name or not department or not grade:
                    st.error("필수 항목을 모두 입력해주세요.")
                else:
                    students_df = get_students()
                    
                    # 중복 학번 체크
                    is_duplicate = False
                    if not students_df.empty and 'student_id' in students_df.columns:
                        is_duplicate = student_id in students_df['student_id'].values
                    
                    if is_duplicate:
                        st.error("이미 등록된 학번입니다.")
                    else:
                        # 새 학생 정보
                        new_student = {
                            "student_id": student_id,
                            "name": name,
                            "department": department,
                            "grade": grade,
                            "email": email,
                            "phone": phone,
                            "noshow_count": 0,
                            "registration_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 데이터 업데이트
                        if students_df.empty:
                            students_df = pd.DataFrame([new_student])
                        else:
                            students_df = pd.concat([students_df, pd.DataFrame([new_student])], ignore_index=True)
                        
                        update_students(students_df)
                        st.success(f"학생 {name}(학번: {student_id})이(가) 등록되었습니다.")
    
    # 학생 검색 탭
    with tab3:
        st.subheader("학생 검색")
        search_option = st.selectbox("검색 기준", ["학번", "성명", "학과"])
        search_text = st.text_input("검색어")
        
        if st.button("검색"):
            if not search_text:
                st.warning("검색어를 입력하세요.")
            else:
                students_df = get_students()
                
                if not students_df.empty:
                    if search_option == "학번":
                        result = students_df[students_df['student_id'].str.contains(search_text)]
                    elif search_option == "성명":
                        result = students_df[students_df['name'].str.contains(search_text)]
                    else:  # "학과"
                        result = students_df[students_df['department'].str.contains(search_text)]
                    
                    if not result.empty:
                        st.dataframe(result)
                    else:
                        st.info("검색 결과가 없습니다.")
                else:
                    st.info("등록된 학생이 없습니다.")

# 특강 관리
elif menu == "특강 관리":
    st.title("📚 특강 관리")
    
    tab1, tab2 = st.tabs(["특강 목록", "특강 등록"])
    
    # 특강 목록 탭
    with tab1:
        st.subheader("등록된 특강 목록")
        lectures_df = get_lectures()
        
        if not lectures_df.empty:
            # 날짜 기준 필터링
            filter_option = st.radio("필터", ["모든 특강", "지난 특강", "다가오는 특강"])
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            if filter_option == "지난 특강":
                filtered_lectures = lectures_df[lectures_df['lecture_date'] < today]
            elif filter_option == "다가오는 특강":
                filtered_lectures = lectures_df[lectures_df['lecture_date'] >= today]
            else:
                filtered_lectures = lectures_df
            
            if not filtered_lectures.empty:
                # 신청 현황 추가
                registrations_df = get_registrations()
                if not registrations_df.empty:
                    lecture_stats = []
                    
                    for _, lecture in filtered_lectures.iterrows():
                        lecture_name = lecture['lecture_name']
                        lecture_regs = registrations_df[registrations_df['lecture_name'] == lecture_name]
                        
                        reg_count = len(lecture_regs)
                        noshow_count = len(lecture_regs[lecture_regs['noshow'] == True]) if 'noshow' in lecture_regs.columns else 0
                        
                        lecture_data = lecture.to_dict()
                        lecture_data['registration_count'] = reg_count
                        lecture_data['noshow_count'] = noshow_count
                        
                        lecture_stats.append(lecture_data)
                    
                    lecture_stats_df = pd.DataFrame(lecture_stats)
                    st.dataframe(lecture_stats_df)
                else:
                    st.dataframe(filtered_lectures)
            else:
                st.info(f"{filter_option}이 없습니다.")
        else:
            st.info("등록된 특강이 없습니다.")
    
    # 특강 등록 탭
    with tab2:
        st.subheader("새 특강 등록")
        
        with st.form("lecture_form"):
            lecture_name = st.text_input("특강명")
            lecture_date = st.date_input("특강 날짜")
            lecture_time = st.time_input("특강 시간")
            location = st.text_input("장소")
            capacity = st.number_input("정원", min_value=1, value=30)
            instructor = st.text_input("강사")
            description = st.text_area("설명")
            
            submitted = st.form_submit_button("특강 등록")
            
            if submitted:
                if not lecture_name or not location or not instructor:
                    st.error("필수 항목을 모두 입력해주세요.")
                else:
                    lectures_df = get_lectures()
                    
                    # 특강 중복 검사
                    is_duplicate = False
                    if not lectures_df.empty:
                        is_duplicate = (
                            (lectures_df['lecture_name'] == lecture_name) & 
                            (lectures_df['lecture_date'] == lecture_date.strftime('%Y-%m-%d'))
                        ).any()
                    
                    if is_duplicate:
                        st.error("동일한 날짜에 같은 이름의 특강이 이미 등록되어 있습니다.")
                    else:
                        # 새 특강 정보
                        new_lecture = {
                            "lecture_id": str(uuid.uuid4()),
                            "lecture_name": lecture_name,
                            "lecture_date": lecture_date.strftime('%Y-%m-%d'),
                            "lecture_time": lecture_time.strftime('%H:%M'),
                            "location": location,
                            "capacity": capacity,
                            "instructor": instructor,
                            "description": description,
                            "registration_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 데이터 업데이트
                        if lectures_df.empty:
                            lectures_df = pd.DataFrame([new_lecture])
                        else:
                            lectures_df = pd.concat([lectures_df, pd.DataFrame([new_lecture])], ignore_index=True)
                        
                        update_lectures(lectures_df)
                        st.success(f"특강 '{lecture_name}'이(가) 등록되었습니다.")

# 신청 관리
elif menu == "신청 관리":
    st.title("📝 신청 관리")
    
    tab1, tab2, tab3 = st.tabs(["신청 내역", "특강 신청", "신청 취소"])
    
    # 신청 내역 탭
    with tab1:
        st.subheader("특강 신청 내역")
        registrations_df = get_registrations()
        
        if not registrations_df.empty:
            # 필터링 옵션
            filter_options = st.multiselect(
                "필터링", 
                ["학번", "특강명", "노쇼 여부"]
            )
            
            filtered_df = registrations_df.copy()
            
            if "학번" in filter_options:
                student_id = st.text_input("학번")
                if student_id:
                    filtered_df = filtered_df[filtered_df['student_id'].str.contains(student_id)]
            
            if "특강명" in filter_options:
                lectures_df = get_lectures()
                if not lectures_df.empty:
                    lecture_names = lectures_df['lecture_name'].unique().tolist()
                    selected_lecture = st.selectbox("특강명", [""] + lecture_names)
                    if selected_lecture:
                        filtered_df = filtered_df[filtered_df['lecture_name'] == selected_lecture]
            
            if "노쇼 여부" in filter_options:
                noshow_status = st.radio("노쇼 여부", ["전체", "노쇼", "출석"])
                if noshow_status != "전체":
                    if 'noshow' in filtered_df.columns:
                        if noshow_status == "노쇼":
                            filtered_df = filtered_df[filtered_df['noshow'] == True]
                        else:  # "출석"
                            filtered_df = filtered_df[filtered_df['noshow'] == False]
            
            if not filtered_df.empty:
                st.dataframe(filtered_df)
            else:
                st.info("조건에 맞는 신청 내역이 없습니다.")
        else:
            st.info("신청 내역이 없습니다.")
    
    # 특강 신청 탭
    with tab2:
        st.subheader("특강 신청")
        
        # 학생 선택
        students_df = get_students()
        if not students_df.empty:
            student_options = students_df.apply(lambda row: f"{row['name']} ({row['student_id']})", axis=1).tolist()
            selected_student = st.selectbox("학생 선택", [""] + student_options)
            
            if selected_student:
                selected_id = selected_student.split("(")[1].split(")")[0]
                selected_name = selected_student.split(" (")[0]
                
                # 특강 선택
                lectures_df = get_lectures()
                if not lectures_df.empty:
                    # 날짜가 지나지 않은 특강만 필터링
                    today = datetime.now().strftime('%Y-%m-%d')
                    available_lectures = lectures_df[lectures_df['lecture_date'] >= today]
                    
                    if not available_lectures.empty:
                        lecture_options = available_lectures.apply(
                            lambda row: f"{row['lecture_name']} ({row['lecture_date']})", axis=1
                        ).tolist()
                        selected_lecture = st.selectbox("특강 선택", [""] + lecture_options)
                        
                        if selected_lecture:
                            lecture_name = selected_lecture.split(" (")[0]
                            lecture_date = selected_lecture.split("(")[1].split(")")[0]
                            
                            # 중복 신청 확인
                            registrations_df = get_registrations()
                            is_duplicate = False
                            
                            if not registrations_df.empty:
                                is_duplicate = (
                                    (registrations_df['student_id'] == selected_id) & 
                                    (registrations_df['lecture_name'] == lecture_name)
                                ).any()
                            
                            if is_duplicate:
                                st.error("이미 신청한 특강입니다.")
                            else:
                                if st.button("신청하기"):
                                    # 신청 정보 생성
                                    new_registration = {
                                        "registration_id": str(uuid.uuid4()),
                                        "student_id": selected_id,
                                        "student_name": selected_name,
                                        "lecture_name": lecture_name,
                                        "lecture_date": lecture_date,
                                        "registration_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        "attendance_checked": False,
                                        "noshow": False
                                    }
                                    
                                    # 데이터 업데이트
                                    if registrations_df.empty:
                                        registrations_df = pd.DataFrame([new_registration])
                                    else:
                                        registrations_df = pd.concat([registrations_df, pd.DataFrame([new_registration])], ignore_index=True)
                                    
                                    update_registrations(registrations_df)
                                    st.success(f"{selected_name} 학생의 '{lecture_name}' 특강 신청이 완료되었습니다.")
                    else:
                        st.info("신청 가능한 특강이 없습니다.")
                else:
                    st.info("등록된 특강이 없습니다.")
        else:
            st.info("등록된 학생이 없습니다. 먼저 학생을 등록해주세요.")
    
    # 신청 취소 탭
    with tab3:
        st.subheader("특강 신청 취소")
        
        # 학생 선택
        students_df = get_students()
        if not students_df.empty:
            student_options = students_df.apply(lambda row: f"{row['name']} ({row['student_id']})", axis=1).tolist()
            selected_student = st.selectbox("학생 선택", [""] + student_options, key="cancel_student")
            
            if selected_student:
                selected_id = selected_student.split("(")[1].split(")")[0]
                
                # 해당 학생의 신청 내역 확인
                registrations_df = get_registrations()
                if not registrations_df.empty:
                    student_registrations = registrations_df[registrations_df['student_id'] == selected_id]
                    
                    if not student_registrations.empty:
                        # 취소할 특강 선택
                        registration_options = student_registrations.apply(
                            lambda row: f"{row['lecture_name']} ({row['lecture_date']})", axis=1
                        ).tolist()
                        selected_registration = st.selectbox("취소할 특강 선택", [""] + registration_options)
                        
                        if selected_registration:
                            lecture_name = selected_registration.split(" (")[0]
                            
                            if st.button("신청 취소"):
                                # 해당 신청 내역 삭제
                                updated_registrations = registrations_df[
                                    ~((registrations_df['student_id'] == selected_id) & 
                                      (registrations_df['lecture_name'] == lecture_name))
                                ]
                                
                                update_registrations(updated_registrations)
                                st.success(f"'{lecture_name}' 특강 신청이 취소되었습니다.")
                    else:
                        st.info("해당 학생의 신청 내역이 없습니다.")
                else:
                    st.info("신청 내역이 없습니다.")
        else:
            st.info("등록된 학생이 없습니다.")

# 출석 체크
elif menu == "출석 체크":
    st.title("✅ 출석 체크")
    
    # 오늘 날짜의 특강 목록
    lectures_df = get_lectures()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not lectures_df.empty:
        today_lectures = lectures_df[lectures_df['lecture_date'] == today]
        
        if not today_lectures.empty:
            # 특강 선택
            lecture_options = today_lectures.apply(
                lambda row: f"{row['lecture_name']} ({row['lecture_time']})", axis=1
            ).tolist()
            selected_lecture = st.selectbox("오늘의 특강 선택", [""] + lecture_options)
            
            if selected_lecture:
                lecture_name = selected_lecture.split(" (")[0]
                
                # 신청자 목록 불러오기
                registrations_df = get_registrations()
                
                if not registrations_df.empty:
                    lecture_registrations = registrations_df[registrations_df['lecture_name'] == lecture_name]
                    
                    if not lecture_registrations.empty:
                        st.subheader(f"{lecture_name} 출석 체크")
                        st.write(f"총 {len(lecture_registrations)}명의 신청자가 있습니다.")
                        
                        # 출석체크 표시
                        for i, reg in lecture_registrations.iterrows():
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                st.write(f"**{reg['student_name']}** (학번: {reg['student_id']})")
                            
                            with col2:
                                if st.button("출석", key=f"attend_{reg['student_id']}"):
                                    # 출석 체크 (노쇼=False)
                                    registrations_df.loc[
                                        (registrations_df['student_id'] == reg['student_id']) & 
                                        (registrations_df['lecture_name'] == lecture_name),
                                        ['attendance_checked', 'noshow']
                                    ] = [True, False]
                                    
                                    update_registrations(registrations_df)
                                    st.success(f"{reg['student_name']} 학생 출석 처리되었습니다.")
                                    st.rerun()
                                
                                if st.button("노쇼", key=f"noshow_{reg['student_id']}"):
                                    # 노쇼 체크 (노쇼=True)
                                    registrations_df.loc[
                                        (registrations_df['student_id'] == reg['student_id']) & 
                                        (registrations_df['lecture_name'] == lecture_name),
                                        ['attendance_checked', 'noshow']
                                    ] = [True, True]
                                    
                                    # 학생의 노쇼 카운트 증가
                                    students_df = get_students()
                                    if not students_df.empty:
                                        students_df.loc[
                                            students_df['student_id'] == reg['student_id'],
                                            'noshow_count'
                                        ] += 1
                                        
                                        update_students(students_df)
                                    
                                    update_registrations(registrations_df)
                                    st.error(f"{reg['student_name']} 학생 노쇼 처리되었습니다.")
                                    st.rerun()
                            
                            # 이미 체크된 경우 상태 표시
                            if 'attendance_checked' in reg and reg['attendance_checked']:
                                if 'noshow' in reg and reg['noshow']:
                                    st.error("노쇼")
                                else:
                                    st.success("출석 완료")
                            
                            st.markdown("---")
                    else:
                        st.info("해당 특강에 신청한 학생이 없습니다.")
                else:
                    st.info("신청 내역이 없습니다.")
        else:
            st.info("오늘 예정된 특강이 없습니다.")
    else:
        st.info("등록된 특강이 없습니다.")

# 노쇼 현황
elif menu == "노쇼 현황":
    st.title("⚠️ 노쇼 현황")
    
    tab1, tab2 = st.tabs(["노쇼 학생 목록", "노쇼 통계"])
    
    # 노쇼 학생 목록 탭
    with tab1:
        st.subheader("노쇼 학생 목록")
        
        registrations_df = get_registrations()
        
        if not registrations_df.empty and 'noshow' in registrations_df.columns:
            noshow_registrations = registrations_df[registrations_df['noshow'] == True]
            
            if not noshow_registrations.empty:
                st.dataframe(noshow_registrations)
                
                # 노쇼 학생 상세 정보
                st.subheader("노쇼 학생 상세 정보")
                
                students_df = get_students()
                if not students_df.empty:
                    # 노쇼 횟수별로 학생 정보 집계
                    student_noshows = noshow_registrations.groupby('student_id').size().reset_index()
                    student_noshows.columns = ['student_id', 'noshow_count']
                    
                    # 학생 정보와 병합
                    student_details = students_df.merge(student_noshows, on='student_id', how='inner')
                    
                    # 노쇼 횟수 내림차순 정렬
                    student_details = student_details.sort_values('noshow_count', ascending=False)
                    
                    st.dataframe(student_details)
            else:
                st.info("노쇼 기록이 없습니다.")
        else:
            st.info("신청 내역이 없거나 노쇼 데이터가 없습니다.")
    
    # 노쇼 통계 탭
    with tab2:
        st.subheader("노쇼 통계")
        
        registrations_df = get_registrations()
        
        if not registrations_df.empty and 'noshow' in registrations_df.columns:
            # 전체 노쇼율
            total_regs = len(registrations_df)
            noshow_regs = len(registrations_df[registrations_df['noshow'] == True])