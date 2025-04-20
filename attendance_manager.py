import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime, timedelta
import uuid
import base64
import io

# 페이지 설정
st.set_page_config(
    page_title="특강 프로그램 출결 관리 시스템",
    page_icon="📚",
    layout="wide"
)

# 데이터 파일 경로
DATA_DIR = "data"
LECTURE_FILE = os.path.join(DATA_DIR, "lectures.json")
STUDENT_FILE = os.path.join(DATA_DIR, "students.json")
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.json")

# 디렉토리 생성
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 상수 정의
ATTENDANCE_STATUS = ["출석", "지각", "결석", "조퇴", "병가", "공결"]
LECTURE_STATUS = ["예정", "진행 중", "종료"]

# 초기 데이터 로드
def load_data():
    # 강의 데이터 로드
    if "lectures" not in st.session_state:
        if os.path.exists(LECTURE_FILE):
            try:
                with open(LECTURE_FILE, "r", encoding="utf-8") as f:
                    st.session_state.lectures = json.load(f)
            except:
                st.session_state.lectures = []
        else:
            st.session_state.lectures = []
    
    # 학생 데이터 로드
    if "students" not in st.session_state:
        if os.path.exists(STUDENT_FILE):
            try:
                with open(STUDENT_FILE, "r", encoding="utf-8") as f:
                    st.session_state.students = json.load(f)
            except:
                st.session_state.students = []
        else:
            st.session_state.students = []
    
    # 출결 데이터 로드
    if "attendance" not in st.session_state:
        if os.path.exists(ATTENDANCE_FILE):
            try:
                with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
                    st.session_state.attendance = json.load(f)
            except:
                st.session_state.attendance = []
        else:
            st.session_state.attendance = []

# 데이터 저장
def save_data():
    # 강의 데이터 저장
    with open(LECTURE_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.lectures, f, ensure_ascii=False, indent=4)
    
    # 학생 데이터 저장
    with open(STUDENT_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.students, f, ensure_ascii=False, indent=4)
    
    # 출결 데이터 저장
    with open(ATTENDANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.attendance, f, ensure_ascii=False, indent=4)

# 날짜 형식 변환 함수
def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None

# 특강 상태 업데이트 함수
def update_lecture_status():
    today = datetime.now().date()
    
    for lecture in st.session_state.lectures:
        start_date = format_date(lecture.get("start_date"))
        end_date = format_date(lecture.get("end_date"))
        
        if start_date and end_date:
            if today < start_date:
                lecture["status"] = "예정"
            elif start_date <= today <= end_date:
                lecture["status"] = "진행 중"
            else:
                lecture["status"] = "종료"
    
    save_data()

# 특강 ID로 특강 정보 가져오기
def get_lecture_by_id(lecture_id):
    for lecture in st.session_state.lectures:
        if lecture["id"] == lecture_id:
            return lecture
    return None

# 학생 ID로 학생 정보 가져오기
def get_student_by_id(student_id):
    for student in st.session_state.students:
        if student["id"] == student_id:
            return student
    return None

# 출결 데이터 가져오기 (특강 ID, 날짜)
def get_attendance_data(lecture_id, date):
    return [a for a in st.session_state.attendance if a["lecture_id"] == lecture_id and a["date"] == date]

# 출결 데이터 가져오기 (특강 ID, 학생 ID)
def get_student_attendance(lecture_id, student_id):
    return [a for a in st.session_state.attendance if a["lecture_id"] == lecture_id and a["student_id"] == student_id]

# 특강 날짜 목록 생성
def generate_lecture_dates(start_date, end_date):
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    return dates

# CSV 파일을 데이터프레임으로 변환
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# 엑셀 파일로 변환
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    processed_data = output.getvalue()
    return processed_data

# 새로운 특강 추가 함수
def add_new_lecture(lecture_data):
    lecture_data["id"] = str(uuid.uuid4())
    st.session_state.lectures.append(lecture_data)
    save_data()
    return lecture_data["id"]

# 새로운 학생 추가 함수
def add_new_student(student_data):
    student_data["id"] = str(uuid.uuid4())
    st.session_state.students.append(student_data)
    save_data()
    return student_data["id"]

# 출결 상태 추가/업데이트 함수
def update_attendance(attendance_data):
    # 기존 출결 데이터 확인
    existing = False
    for i, a in enumerate(st.session_state.attendance):
        if (a["lecture_id"] == attendance_data["lecture_id"] and 
            a["student_id"] == attendance_data["student_id"] and 
            a["date"] == attendance_data["date"]):
            st.session_state.attendance[i] = attendance_data
            existing = True
            break
    
    # 새 출결 데이터 추가
    if not existing:
        attendance_data["id"] = str(uuid.uuid4())
        st.session_state.attendance.append(attendance_data)
    
    save_data()

# 학생 출석률 계산
def calculate_attendance_rate(lecture_id, student_id):
    attendances = get_student_attendance(lecture_id, student_id)
    if not attendances:
        return {"출석": 0, "지각": 0, "결석": 0, "조퇴": 0, "병가": 0, "공결": 0, "출석률": 0}
    
    total = len(attendances)
    status_counts = {status: 0 for status in ATTENDANCE_STATUS}
    
    for a in attendances:
        status_counts[a["status"]] += 1
    
    # 출석률 계산 (출석 + 지각 + 공결 + 병가) / 전체
    attendance_rate = (status_counts["출석"] + status_counts["지각"] + 
                      status_counts["공결"] + status_counts["병가"]) / total * 100 if total > 0 else 0
    
    status_counts["출석률"] = round(attendance_rate, 1)
    return status_counts

# 특강 전체 출석 현황
def get_lecture_attendance_summary(lecture_id):
    lecture = get_lecture_by_id(lecture_id)
    if not lecture:
        return pd.DataFrame()
    
    start_date = format_date(lecture["start_date"])
    end_date = format_date(lecture["end_date"])
    today = datetime.now().date()
    
    if end_date > today:
        end_date = today
    
    if start_date > today:
        return pd.DataFrame()
    
    dates = generate_lecture_dates(start_date, end_date)
    
    # 특강에 등록된 학생 목록
    students = [s for s in st.session_state.students if lecture_id in s.get("enrolled_lectures", [])]
    
    # 결과 데이터
    results = []
    
    for student in students:
        student_id = student["id"]
        attendance_data = get_student_attendance(lecture_id, student_id)
        
        # 각 날짜별 출석 상태 정리
        attendance_by_date = {a["date"]: a["status"] for a in attendance_data}
        
        # 학생별 출결 요약
        student_summary = {
            "학생ID": student_id,
            "이름": student["name"],
            "학번": student["student_id"],
            "학과": student["department"]
        }
        
        # 날짜별 출석 상태 추가
        for date in dates:
            student_summary[date] = attendance_by_date.get(date, "미입력")
        
        # 출석 통계 추가
        rate_data = calculate_attendance_rate(lecture_id, student_id)
        student_summary.update({
            "출석": rate_data["출석"],
            "지각": rate_data["지각"],
            "결석": rate_data["결석"],
            "조퇴": rate_data["조퇴"],
            "병가": rate_data["병가"],
            "공결": rate_data["공결"],
            "출석률": f"{rate_data['출석률']}%"
        })
        
        results.append(student_summary)
    
    return pd.DataFrame(results)

# 로드 데이터
load_data()
update_lecture_status()

# 사이드바 메뉴
st.sidebar.title("특강 출결 관리 시스템")
menu = st.sidebar.radio("메뉴", ["대시보드", "특강 관리", "학생 관리", "출결 관리", "통계 및 보고서", "설정"])

# 대시보드
if menu == "대시보드":
    st.title("📚 특강 프로그램 출결 관리 대시보드")
    
    # 요약 정보 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("등록된 특강 수", len(st.session_state.lectures))
    
    with col2:
        st.metric("등록된 학생 수", len(st.session_state.students))
    
    with col3:
        ongoing_lectures = len([l for l in st.session_state.lectures if l["status"] == "진행 중"])
        st.metric("진행 중인 특강", ongoing_lectures)
    
    # 진행 중인 특강 표시
    st.subheader("🔍 진행 중인 특강")
    ongoing_lectures = [l for l in st.session_state.lectures if l["status"] == "진행 중"]
    
    if not ongoing_lectures:
        st.info("현재 진행 중인 특강이 없습니다.")
    else:
        for lecture in ongoing_lectures:
            with st.expander(f"{lecture['name']} ({lecture['start_date']} ~ {lecture['end_date']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**강사:** {lecture['instructor']}")
                    st.write(f"**장소:** {lecture['location']}")
                    st.write(f"**시간:** {lecture['start_time']} ~ {lecture['end_time']}")
                
                with col2:
                    enrolled_students = len([s for s in st.session_state.students if lecture["id"] in s.get("enrolled_lectures", [])])
                    st.write(f"**등록 학생 수:** {enrolled_students}명")
                    
                    # 오늘 출석 현황
                    today = datetime.now().strftime("%Y-%m-%d")
                    today_attendance = get_attendance_data(lecture["id"], today)
                    attendance_count = len([a for a in today_attendance if a["status"] == "출석"])
                    late_count = len([a for a in today_attendance if a["status"] == "지각"])
                    absent_count = len([a for a in today_attendance if a["status"] == "결석"])
                    
                    st.write(f"**오늘 출석 현황:** 출석 {attendance_count}명, 지각 {late_count}명, 결석 {absent_count}명")
                
                # 출석 체크 바로가기 버튼
                if st.button(f"{lecture['name']} 출석체크 바로가기", key=f"goto_attendance_{lecture['id']}"):
                    st.session_state.selected_lecture = lecture["id"]
                    st.session_state.selected_date = today
                    st.session_state.menu = "출결 관리"
                    st.rerun()
    
    # 오늘 출석체크 필요한 특강 알림
    st.subheader("⚠️ 알림")
    today = datetime.now().strftime("%Y-%m-%d")
    
    attendance_required = []
    for lecture in ongoing_lectures:
        today_attendance = get_attendance_data(lecture["id"], today)
        enrolled_students = [s for s in st.session_state.students if lecture["id"] in s.get("enrolled_lectures", [])]
        
        if len(today_attendance) < len(enrolled_students):
            attendance_required.append({
                "lecture_id": lecture["id"],
                "name": lecture["name"],
                "instructor": lecture["instructor"],
                "time": f"{lecture['start_time']} ~ {lecture['end_time']}",
                "enrolled": len(enrolled_students),
                "checked": len(today_attendance)
            })
    
    if attendance_required:
        st.warning("다음 특강들의 오늘 출석체크가 완료되지 않았습니다.")
        for lec in attendance_required:
            st.write(f"📝 **{lec['name']}** (강사: {lec['instructor']}, 시간: {lec['time']})")
            st.write(f"   등록 인원: {lec['enrolled']}명, 출석체크 완료: {lec['checked']}명")
            
            if st.button(f"{lec['name']} 출석체크 바로가기", key=f"goto_missing_{lec['lecture_id']}"):
                st.session_state.selected_lecture = lec["lecture_id"]
                st.session_state.selected_date = today
                st.session_state.menu = "출결 관리"
                st.rerun()
    else:
        st.success("모든 진행 중인 특강의 오늘 출석체크가 완료되었습니다.")
    
    # 최근 추가된 특강
    st.subheader("📅 예정된 특강")
    upcoming_lectures = [l for l in st.session_state.lectures if l["status"] == "예정"]
    
    if not upcoming_lectures:
        st.info("예정된 특강이 없습니다.")
    else:
        # 시작일 기준 정렬
        upcoming_lectures.sort(key=lambda x: x["start_date"])
        
        for lecture in upcoming_lectures[:3]:  # 가장 빠른 3개만 표시
            start_date = format_date(lecture["start_date"])
            days_to_start = (start_date - datetime.now().date()).days
            
            st.write(f"📚 **{lecture['name']}** - {days_to_start}일 후 시작")
            st.write(f"   {lecture['start_date']} ~ {lecture['end_date']} | 강사: {lecture['instructor']}")

# 특강 관리
elif menu == "특강 관리":
    st.title("📚 특강 관리")
    
    tab1, tab2 = st.tabs(["특강 목록", "특강 등록"])
    
    # 특강 목록 탭
    # 특강 목록 탭의 코드를 다음과 같이 수정하세요
# 위치: "특강 관리" 메뉴의 "특강 목록" 탭 내 코드

    with tab1:
        st.subheader("등록된 특강 목록")
        
        # 세션 상태 변수 초기화 (삭제 확인을 위한 변수)
        if "lecture_to_delete" not in st.session_state:
            st.session_state["lecture_to_delete"] = None
        
        # 필터 옵션
        status_filter = st.multiselect("상태 필터", LECTURE_STATUS, default=LECTURE_STATUS)
        search_query = st.text_input("검색 (특강명, 강사명)")
        
        # 필터링된 특강 목록
        filtered_lectures = [l for l in st.session_state.lectures if l["status"] in status_filter]
        
        if search_query:
            filtered_lectures = [
                l for l in filtered_lectures 
                if search_query.lower() in l["name"].lower() or 
                search_query.lower() in l["instructor"].lower()
            ]
        
        # 특강 표시
        if not filtered_lectures:
            st.info("등록된 특강이 없거나 필터 조건에 맞는 특강이 없습니다.")
        else:
            for i, lecture in enumerate(filtered_lectures):
                with st.expander(f"{lecture['name']} ({lecture['start_date']} ~ {lecture['end_date']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**특강 ID:** {lecture['id']}")
                        st.write(f"**강사:** {lecture['instructor']}")
                        st.write(f"**일정:** {lecture['start_date']} ~ {lecture['end_date']}")
                        st.write(f"**시간:** {lecture['start_time']} ~ {lecture['end_time']}")
                        st.write(f"**장소:** {lecture['location']}")
                        st.write(f"**상태:** {lecture['status']}")
                    
                    with col2:
                        st.write("**특강 설명:**")
                        st.write(lecture["description"])
                        
                        # 등록된 학생 수
                        enrolled_students = len([s for s in st.session_state.students if lecture["id"] in s.get("enrolled_lectures", [])])
                        st.write(f"**등록 학생 수:** {enrolled_students}명")
                    
                    # 버튼 행
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # 특강 수정 버튼
                        if st.button("특강 수정", key=f"edit_lecture_{i}"):
                            st.session_state.edit_lecture = lecture
                            st.rerun()
                    
                    with col2:
                        # 특강 삭제 버튼
                        if st.button("특강 삭제", key=f"delete_lecture_{i}"):
                            st.session_state["lecture_to_delete"] = lecture["id"]
                            st.rerun()
                    
                    with col3:
                        # 학생 등록 관리 버튼
                        if st.button("학생 등록 관리", key=f"manage_students_{i}"):
                            st.session_state.manage_lecture_students = lecture["id"]
                            st.rerun()
                    
                    # 삭제 확인 다이얼로그
                    if st.session_state["lecture_to_delete"] == lecture["id"]:
                        st.warning(f"정말로 '{lecture['name']}' 특강을 삭제하시겠습니까?")
                        
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button("취소", key=f"cancel_delete_{i}"):
                                st.session_state["lecture_to_delete"] = None
                                st.rerun()
                        
                        with confirm_col2:
                            if st.button("삭제 확인", key=f"confirm_delete_{i}"):
                                # 특강 관련 출결 데이터 삭제
                                st.session_state.attendance = [a for a in st.session_state.attendance if a["lecture_id"] != lecture["id"]]
                                
                                # 학생 등록 정보에서 제거
                                for student in st.session_state.students:
                                    if "enrolled_lectures" in student and lecture["id"] in student["enrolled_lectures"]:
                                        student["enrolled_lectures"].remove(lecture["id"])
                                
                                # 특강 삭제
                                st.session_state.lectures.remove(lecture)
                                save_data()
                                st.success(f"{lecture['name']} 특강이 삭제되었습니다.")
                                st.session_state["lecture_to_delete"] = None
                                st.rerun()
        
        # 학생 등록 관리
        if "manage_lecture_students" in st.session_state:
            lecture_id = st.session_state.manage_lecture_students
            lecture = get_lecture_by_id(lecture_id)
            
            if lecture:
                st.subheader(f"{lecture['name']} - 학생 등록 관리")
                
                # 학생 목록
                all_students = st.session_state.students
                
                # 이미 등록된 학생 IDs
                enrolled_students = [s for s in all_students if lecture_id in s.get("enrolled_lectures", [])]
                enrolled_ids = [s["id"] for s in enrolled_students]
                
                # 미등록 학생 목록
                unenrolled_students = [s for s in all_students if s["id"] not in enrolled_ids]
                
                # 학생 검색
                search_student = st.text_input("학생 검색 (이름, 학번)")
                
                if search_student:
                    unenrolled_students = [
                        s for s in unenrolled_students 
                        if search_student.lower() in s["name"].lower() or 
                           search_student.lower() in s["student_id"].lower()
                    ]
                
                # 학생 선택 및 등록
                selected_students = st.multiselect(
                    "등록할 학생 선택",
                    options=[f"{s['name']} ({s['student_id']})" for s in unenrolled_students],
                    format_func=lambda x: x
                )
                
                if st.button("선택한 학생 등록") and selected_students:
                    for selected in selected_students:
                        # 이름과 학번에서 학생 검색
                        name = selected.split(" (")[0]
                        student_id_number = selected.split("(")[1].replace(")", "")
                        
                        for s in unenrolled_students:
                            if s["name"] == name and s["student_id"] == student_id_number:
                                if "enrolled_lectures" not in s:
                                    s["enrolled_lectures"] = []
                                s["enrolled_lectures"].append(lecture_id)
                                break
                    
                    save_data()
                    st.success(f"{len(selected_students)}명의 학생이 {lecture['name']} 특강에 등록되었습니다.")
                    st.rerun()
                
                # 이미 등록된 학생 목록
                st.subheader("등록된 학생 목록")
                
                if not enrolled_students:
                    st.info("현재 등록된 학생이 없습니다.")
                else:
                    enrolled_df = pd.DataFrame([
                        {"이름": s["name"], "학번": s["student_id"], "학과": s["department"], "학년": s["grade"], "ID": s["id"]}
                        for s in enrolled_students
                    ])
                    
                    # 등록된 학생 테이블 표시
                    st.dataframe(enrolled_df[["이름", "학번", "학과", "학년"]], use_container_width=True)
                    
                    # 학생 등록 취소
                    students_to_remove = st.multiselect(
                        "등록 취소할 학생 선택",
                        options=[f"{s['name']} ({s['student_id']})" for s in enrolled_students],
                        format_func=lambda x: x
                    )
                    
                    if st.button("선택한 학생 등록 취소") and students_to_remove:
                        for selected in students_to_remove:
                            # 이름과 학번에서 학생 검색
                            name = selected.split(" (")[0]
                            student_id_number = selected.split("(")[1].replace(")", "")
                            
                            for s in enrolled_students:
                                if s["name"] == name and s["student_id"] == student_id_number:
                                    if "enrolled_lectures" in s and lecture_id in s["enrolled_lectures"]:
                                        s["enrolled_lectures"].remove(lecture_id)
                                    break
                        
                        save_data()
                        st.success(f"{len(students_to_remove)}명의 학생 등록이 취소되었습니다.")
                        st.rerun()
                
                # 돌아가기 버튼
                if st.button("학생 등록 관리 종료"):
                    del st.session_state.manage_lecture_students
                    st.rerun()
        
        # 특강 수정 폼
        if "edit_lecture" in st.session_state:
            lecture = st.session_state.edit_lecture
            st.subheader(f"특강 수정: {lecture['name']}")
            
            with st.form("edit_lecture_form"):
                name = st.text_input("특강명", value=lecture["name"])
                instructor = st.text_input("강사명", value=lecture["instructor"])
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("시작일", value=datetime.strptime(lecture["start_date"], "%Y-%m-%d"))
                    start_time = st.time_input("시작 시간", value=datetime.strptime(lecture["start_time"], "%H:%M").time())
                
                with col2:
                    end_date = st.date_input("종료일", value=datetime.strptime(lecture["end_date"], "%Y-%m-%d"))
                    end_time = st.time_input("종료 시간", value=datetime.strptime(lecture["end_time"], "%H:%M").time())
                
                location = st.text_input("장소", value=lecture["location"])
                description = st.text_area("설명", value=lecture["description"])
                status = st.selectbox("상태", options=LECTURE_STATUS, index=LECTURE_STATUS.index(lecture["status"]))
                
                submitted = st.form_submit_button("특강 정보 수정")
                
                if submitted:
                    # 입력 검증
                    if not name or not instructor or not location:
                        st.error("특강명, 강사명, 장소는 필수 항목입니다.")
                    elif start_date > end_date:
                        st.error("종료일은 시작일 이후여야 합니다.")
                    else:
                        # 특강 정보 업데이트
                        updated_lecture = {
                            "id": lecture["id"],
                            "name": name,
                            "instructor": instructor,
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d"),
                            "start_time": start_time.strftime("%H:%M"),
                            "end_time": end_time.strftime("%H:%M"),
                            "location": location,
                            "description": description,
                            "status": status
                        }
                        
                        # 특강 정보 업데이트
                        for i, lec in enumerate(st.session_state.lectures):
                            if lec["id"] == lecture["id"]:
                                st.session_state.lectures[i] = updated_lecture
                                break
                        
                        save_data()
                        st.success(f"{name} 특강 정보가 수정되었습니다.")
                        del st.session_state.edit_lecture
                        st.rerun()
            
            # 취소 버튼
            if st.button("수정 취소"):
                del st.session_state.edit_lecture
                st.rerun()
    
    # 특강 등록 탭
    # 특강 등록 탭 부분 수정 (아래 코드로 교체)
    # 특강 등록 탭 (이 부분이 추가/수정된 내용입니다)
    with tab2:
        st.subheader("새 특강 등록")

        with st.form("add_lecture_form"):
            # 특강 정보 입력 필드
            name = st.text_input("특강명")
            instructor = st.text_input("강사명")

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("시작일", value=datetime.now())
                start_time = st.time_input("시작 시간", value=datetime.strptime("09:00", "%H:%M").time())

            with col2:
                end_date = st.date_input("종료일", value=datetime.now())
                end_time = st.time_input("종료 시간", value=datetime.strptime("18:00", "%H:%M").time())

            location = st.text_input("장소")
            description = st.text_area("설명")

            # 폼 제출 버튼
            submitted = st.form_submit_button("특강 등록")

            if submitted:
                # 입력값 검증
                if not name or not instructor or not location:
                    st.error("특강명, 강사명, 장소는 필수 입력 항목입니다.")
                elif start_date > end_date:
                    st.error("종료일은 시작일보다 빠를 수 없습니다.")
                else:
                    # 새 특강 데이터 생성
                    new_lecture_data = {
                        "name": name,
                        "instructor": instructor,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "start_time": start_time.strftime("%H:%M"),
                        "end_time": end_time.strftime("%H:%M"),
                        "location": location,
                        "description": description,
                        "status": "예정" # 초기 상태는 '예정'으로 설정
                    }

                    # 특강 추가 함수 호출
                    lecture_id = add_new_lecture(new_lecture_data)
                    update_lecture_status() # 상태 즉시 업데이트
                    st.success(f"'{name}' 특강이 성공적으로 등록되었습니다. (ID: {lecture_id})")
                    # st.rerun() # 필요시 폼 초기화를 위해 주석 해제
# 위치: "특강 관리" 메뉴의 "특강 등록" 탭 내부

    

# 학생 관리
elif menu == "학생 관리":
    st.title("👨‍🎓 학생 관리")
    
    tab1, tab2, tab3 = st.tabs(["학생 목록", "학생 등록", "CSV 일괄 등록"])
    
    # 학생 목록 탭
    with tab1:
        st.subheader("등록된 학생 목록")
        
        # 검색 및 필터
        search_query = st.text_input("검색 (이름, 학번, 학과)")
        
        # 필터링된 학생 목록
        filtered_students = st.session_state.students
        
        if search_query:
            filtered_students = [
                s for s in filtered_students 
                if search_query.lower() in s["name"].lower() or 
                   search_query.lower() in s["student_id"].lower() or
                   search_query.lower() in s["department"].lower()
            ]
        
        # 학생 목록 표시
        if not filtered_students:
            st.info("등록된 학생이 없거나 검색 조건에 맞는 학생이 없습니다.")
        else:
            # 페이지네이션
            students_per_page = 10
            total_pages = (len(filtered_students) + students_per_page - 1) // students_per_page
            
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                page = st.number_input("페이지", min_value=1, max_value=max(1, total_pages), value=1, step=1)
            
            start_idx = (page - 1) * students_per_page
            end_idx = min(start_idx + students_per_page, len(filtered_students))
            
            page_students = filtered_students[start_idx:end_idx]
            
            for i, student in enumerate(page_students):
                with st.expander(f"{student['name']} ({student['student_id']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**학생 ID:** {student['id']}")
                        st.write(f"**이름:** {student['name']}")
                        st.write(f"**학번:** {student['student_id']}")
                        st.write(f"**학과:** {student['department']}")
                        st.write(f"**학년:** {student['grade']}")
                    
                    with col2:
                        st.write(f"**연락처:** {student.get('phone', '-')}")
                        st.write(f"**이메일:** {student.get('email', '-')}")
                        
                        # 등록된 특강 목록
                        enrolled_lectures = []
                        if "enrolled_lectures" in student:
                            for lecture_id in student["enrolled_lectures"]:
                                lecture = get_lecture_by_id(lecture_id)
                                if lecture:
                                    enrolled_lectures.append(lecture["name"])
                        
                        if enrolled_lectures:
                            st.write("**등록된 특강:**")
                            for lec_name in enrolled_lectures:
                                st.write(f"- {lec_name}")
                        else:
                            st.write("**등록된 특강:** 없음")
                    
                    # 학생 수정 버튼
                    if st.button("학생 정보 수정", key=f"edit_student_{i}"):
                        st.session_state.edit_student = student
                        st.rerun()
                    
                    # 학생 삭제 버튼
                    if st.button("학생 삭제", key=f"delete_student_{i}"):
                        # 학생 삭제 전 확인
                        if st.checkbox(f"{student['name']} 학생을 정말 삭제하시겠습니까?", key=f"confirm_delete_student_{i}"):
                            # 학생 관련 출결 데이터 삭제
                            st.session_state.attendance = [a for a in st.session_state.attendance if a["student_id"] != student["id"]]
                            
                            # 학생 삭제
                            st.session_state.students.remove(student)
                            save_data()
                            st.success(f"{student['name']} 학생이 삭제되었습니다.")
                            st.rerun()
        
        # 학생 수정 폼
        if "edit_student" in st.session_state:
            student = st.session_state.edit_student
            st.subheader(f"학생 정보 수정: {student['name']}")
            
            with st.form("edit_student_form"):
                name = st.text_input("이름", value=student["name"])
                student_id_number = st.text_input("학번", value=student["student_id"])
                department = st.text_input("학과", value=student["department"])
                grade = st.selectbox("학년", options=["1", "2", "3", "4", "대학원"], index=["1", "2", "3", "4", "대학원"].index(student["grade"]))
                phone = st.text_input("연락처", value=student.get("phone", ""))
                email = st.text_input("이메일", value=student.get("email", ""))
                
                submitted = st.form_submit_button("학생 정보 수정")
                
                if submitted:
                    # 입력 검증
                    if not name or not student_id_number or not department:
                        st.error("이름, 학번, 학과는 필수 항목입니다.")
                    else:
                        # 학생 정보 업데이트
                        updated_student = {
                            "id": student["id"],
                            "name": name,
                            "student_id": student_id_number,
                            "department": department,
                            "grade": grade,
                            "phone": phone,
                            "email": email
                        }
                        
                        # 등록된 특강 정보 유지
                        if "enrolled_lectures" in student:
                            updated_student["enrolled_lectures"] = student["enrolled_lectures"]
                        
                        # 학생 정보 업데이트
                        for i, s in enumerate(st.session_state.students):
                            if s["id"] == student["id"]:
                                st.session_state.students[i] = updated_student
                                break
                        
                        save_data()
                        st.success(f"{name} 학생 정보가 수정되었습니다.")
                        del st.session_state.edit_student
                        st.rerun()
            
            # 취소 버튼
            if st.button("수정 취소"):
                del st.session_state.edit_student
                st.rerun()
    
    # 학생 등록 탭
    with tab2:
        st.subheader("새 학생 등록")
        
        with st.form("add_student_form"):
            name = st.text_input("이름")
            student_id_number = st.text_input("학번")
            department = st.text_input("학과")
            grade = st.selectbox("학년", options=["1", "2", "3", "4", "대학원"])
            phone = st.text_input("연락처")
            email = st.text_input("이메일")
            
            # 특강 등록 옵션
            available_lectures = [(l["id"], f"{l['name']} ({l['instructor']})") for l in st.session_state.lectures]
            selected_lectures = st.multiselect(
                "등록할 특강",
                options=[l[1] for l in available_lectures],
                format_func=lambda x: x
            )
            
            submitted = st.form_submit_button("학생 등록")
            
            if submitted:
                # 입력 검증
                if not name or not student_id_number or not department:
                    st.error("이름, 학번, 학과는 필수 항목입니다.")
                else:
                    # 특강 ID 매핑
                    enrolled_lecture_ids = []
                    for selected in selected_lectures:
                        for l_id, l_name in available_lectures:
                            if l_name == selected:
                                enrolled_lecture_ids.append(l_id)
                                break
                    
                    # 학생 정보 생성
                    new_student = {
                        "name": name,
                        "student_id": student_id_number,
                        "department": department,
                        "grade": grade,
                        "phone": phone,
                        "email": email,
                        "enrolled_lectures": enrolled_lecture_ids
                    }
                    
                    # 학생 추가
                    student_id = add_new_student(new_student)
                    st.success(f"{name} 학생이 등록되었습니다.")
                    st.rerun()
    
    # CSV 일괄 등록 탭
    with tab3:
        st.subheader("CSV 파일을 통한 학생 일괄 등록")
        
        st.write("CSV 파일 형식: 이름, 학번, 학과, 학년, 연락처, 이메일")
        st.write("예: 홍길동, 20230001, 컴퓨터공학과, 3, 010-1234-5678, hong@example.com")
        
        # 샘플 CSV 다운로드
        sample_data = pd.DataFrame({
            "이름": ["홍길동", "김철수", "이영희"],
            "학번": ["20230001", "20230002", "20230003"],
            "학과": ["컴퓨터공학과", "경영학과", "전자공학과"],
            "학년": ["3", "2", "4"],
            "연락처": ["010-1234-5678", "010-2345-6789", "010-3456-7890"],
            "이메일": ["hong@example.com", "kim@example.com", "lee@example.com"]
        })
        
        csv = convert_df_to_csv(sample_data)
        st.download_button(
            label="샘플 CSV 다운로드",
            data=csv,
            file_name="학생정보_샘플.csv",
            mime="text/csv"
        )
        
        # CSV 파일 업로드
        uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
                
                # 필수 컬럼 확인
                required_columns = ["이름", "학번", "학과", "학년"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}")
                else:
                    # 데이터 미리보기
                    st.write("데이터 미리보기:")
                    st.dataframe(df)
                    
                    # 특강 등록 옵션
                    available_lectures = [(l["id"], f"{l['name']} ({l['instructor']})") for l in st.session_state.lectures]
                    selected_lectures = st.multiselect(
                        "모든 학생을 등록할 특강",
                        options=[l[1] for l in available_lectures],
                        format_func=lambda x: x
                    )
                    
                    # 특강 ID 매핑
                    enrolled_lecture_ids = []
                    for selected in selected_lectures:
                        for l_id, l_name in available_lectures:
                            if l_name == selected:
                                enrolled_lecture_ids.append(l_id)
                                break
                    
                    # 등록 버튼
                    if st.button("학생 일괄 등록"):
                        # 기존 학번 확인 (중복 방지)
                        existing_student_ids = [s["student_id"] for s in st.session_state.students]
                        
                        # 새 학생 등록
                        new_students = []
                        duplicates = []
                        
                        for _, row in df.iterrows():
                            # 필수 필드 확인
                            if pd.isna(row["이름"]) or pd.isna(row["학번"]) or pd.isna(row["학과"]) or pd.isna(row["학년"]):
                                continue
                            
                            # 중복 확인
                            if str(row["학번"]) in existing_student_ids:
                                duplicates.append(row["이름"])
                                continue
                            
                            # 학생 정보 생성
                            new_student = {
                                "name": row["이름"],
                                "student_id": str(row["학번"]),
                                "department": row["학과"],
                                "grade": str(row["학년"]),
                                "phone": str(row["연락처"]) if "연락처" in row and not pd.isna(row["연락처"]) else "",
                                "email": row["이메일"] if "이메일" in row and not pd.isna(row["이메일"]) else "",
                                "enrolled_lectures": enrolled_lecture_ids
                            }
                            
                            # 학생 추가
                            student_id = add_new_student(new_student)
                            new_students.append(row["이름"])
                            existing_student_ids.append(str(row["학번"]))
                        
                        if new_students:
                            st.success(f"{len(new_students)}명의 학생이 등록되었습니다.")
                        
                        if duplicates:
                            st.warning(f"{len(duplicates)}명의 학생은 이미 존재하여 등록되지 않았습니다: {', '.join(duplicates[:5])}" + 
                                      (f" 외 {len(duplicates)-5}명" if len(duplicates) > 5 else ""))
                        
                        st.rerun()
            
            except Exception as e:
                st.error(f"CSV 파일 처리 중 오류가 발생했습니다: {e}")

# 출결 관리
elif menu == "출결 관리":
    st.title("📝 출결 관리")
    
    # 특강 선택
    lecture_options = [(l["id"], f"{l['name']} ({l['instructor']})") for l in st.session_state.lectures]
    
    # 특강 선택 (이전에 선택한 특강 유지)
    selected_lecture_id = None
    if "selected_lecture" in st.session_state:
        selected_lecture_id = st.session_state.selected_lecture
        selected_lecture_index = 0
        for i, (l_id, _) in enumerate(lecture_options):
            if l_id == selected_lecture_id:
                selected_lecture_index = i
                break
        
        lecture_selection = st.selectbox(
            "특강 선택",
            options=[l[1] for l in lecture_options],
            index=selected_lecture_index,
            format_func=lambda x: x
        )
    else:
        lecture_selection = st.selectbox(
            "특강 선택",
            options=[l[1] for l in lecture_options],
            format_func=lambda x: x
        )
    
    # 선택된 특강 ID 가져오기
    for l_id, l_name in lecture_options:
        if l_name == lecture_selection:
            selected_lecture_id = l_id
            st.session_state.selected_lecture = l_id
            break
    
    if selected_lecture_id:
        lecture = get_lecture_by_id(selected_lecture_id)
        
        if lecture:
            st.subheader(f"{lecture['name']} 출결 관리")
            
            # 날짜 선택
            start_date = format_date(lecture["start_date"])
            end_date = format_date(lecture["end_date"])
            today = datetime.now().date()
            
            # 선택 가능한 날짜 범위
            available_dates = generate_lecture_dates(start_date, min(end_date, today))
            
            # 날짜 선택 (이전에 선택한 날짜 유지)
            if "selected_date" in st.session_state and st.session_state.selected_date in available_dates:
                selected_date_index = available_dates.index(st.session_state.selected_date)
                selected_date = st.selectbox("날짜 선택", options=available_dates, index=selected_date_index)
            else:
                selected_date = st.selectbox("날짜 선택", options=available_dates, index=len(available_dates)-1 if available_dates else 0)
            
            # 선택한 날짜 저장
            st.session_state.selected_date = selected_date
            
            if selected_date:
                # 해당 특강에 등록된 학생 목록
                enrolled_students = [s for s in st.session_state.students if selected_lecture_id in s.get("enrolled_lectures", [])]
                
                if not enrolled_students:
                    st.info("이 특강에 등록된 학생이 없습니다. '학생 관리' 메뉴에서 학생을 등록해주세요.")
                else:
                    # 기존 출결 데이터 가져오기
                    attendance_data = get_attendance_data(selected_lecture_id, selected_date)
                    
                    # 학생별 출결 상태 딕셔너리
                    attendance_dict = {a["student_id"]: a["status"] for a in attendance_data}
                    
                    # 출결 기록 시간 딕셔너리
                    attendance_time_dict = {a["student_id"]: a.get("time", "") for a in attendance_data}
                    
                    # 사유 딕셔너리
                    reason_dict = {a["student_id"]: a.get("reason", "") for a in attendance_data}
                    
                    # 탭 구성
                    tab1, tab2 = st.tabs(["출석 체크", "일괄 출석 처리"])
                    
                    # 개별 출석 체크 탭
                    with tab1:
                        for i, student in enumerate(enrolled_students):
                            with st.expander(f"{student['name']} ({student['student_id']} - {student['department']})"):
                                student_id = student["id"]
                                
                                col1, col2 = st.columns([2, 3])
                                
                                with col1:
                                    # 현재 출결 상태
                                    current_status = attendance_dict.get(student_id, "미입력")
                                    status_index = ATTENDANCE_STATUS.index(current_status) if current_status in ATTENDANCE_STATUS else 0
                                    
                                    # 출결 상태 선택
                                    new_status = st.selectbox(
                                        "출결 상태",
                                        options=ATTENDANCE_STATUS,
                                        index=status_index,
                                        key=f"status_{i}"
                                    )
                                    
                                    # 출석 시간 (현재 시간 기본값)
                                    attendance_time = st.time_input(
                                        "시간",
                                        value=datetime.strptime(attendance_time_dict.get(student_id, datetime.now().strftime("%H:%M")), "%H:%M").time() if attendance_time_dict.get(student_id) else datetime.now().time(),
                                        key=f"time_{i}"
                                    )
                                
                                with col2:
                                    # 사유 입력 (결석, 지각, 조퇴, 병가, 공결인 경우)
                                    if new_status in ["결석", "지각", "조퇴", "병가", "공결"]:
                                        reason = st.text_area(
                                            "사유",
                                            value=reason_dict.get(student_id, ""),
                                            key=f"reason_{i}"
                                        )
                                    else:
                                        reason = ""
                                
                                # 출결 저장 버튼
                                if st.button("저장", key=f"save_{i}"):
                                    # 출결 데이터 생성
                                    new_attendance = {
                                        "lecture_id": selected_lecture_id,
                                        "student_id": student_id,
                                        "date": selected_date,
                                        "status": new_status,
                                        "time": attendance_time.strftime("%H:%M"),
                                        "reason": reason
                                    }
                                    
                                    # 출결 데이터 업데이트
                                    update_attendance(new_attendance)
                                    st.success(f"{student['name']} 출결 정보가 저장되었습니다.")
                                    st.rerun()
                    
                    # 일괄 출석 처리 탭
                    with tab2:
                        st.subheader("일괄 출석 처리")
                        
                        # 선택할 학생 목록 생성
                        student_options = [f"{s['name']} ({s['student_id']})" for s in enrolled_students]
                        student_ids = [s["id"] for s in enrolled_students]
                        
                        # 미입력 학생만 표시 옵션
                        show_only_missing = st.checkbox("미입력 학생만 표시", value=True)
                        
                        if show_only_missing:
                            # 미입력 학생 필터링
                            missing_indices = [i for i, s_id in enumerate(student_ids) if s_id not in attendance_dict]
                            filtered_options = [student_options[i] for i in missing_indices]
                            filtered_ids = [student_ids[i] for i in missing_indices]
                        else:
                            filtered_options = student_options
                            filtered_ids = student_ids
                        
                        # 학생 선택
                        selected_students = st.multiselect(
                            "학생 선택",
                            options=filtered_options,
                            default=filtered_options,  # 기본으로 모두 선택
                            format_func=lambda x: x
                        )
                        
                        # 선택한 학생 ID 목록
                        selected_student_ids = []
                        for selected in selected_students:
                            idx = filtered_options.index(selected)
                            selected_student_ids.append(filtered_ids[idx])
                        
                        # 일괄 처리 설정
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            bulk_status = st.selectbox("출결 상태", options=ATTENDANCE_STATUS)
                        
                        with col2:
                            bulk_time = st.time_input("시간", value=datetime.now().time())
                        
                        # 사유 입력 (결석, 지각, 조퇴, 병가, 공결인 경우)
                        if bulk_status in ["결석", "지각", "조퇴", "병가", "공결"]:
                            bulk_reason = st.text_area("사유")
                        else:
                            bulk_reason = ""
                        
                        # 일괄 처리 버튼
                        if st.button("일괄 처리") and selected_student_ids:
                            for student_id in selected_student_ids:
                                # 출결 데이터 생성
                                new_attendance = {
                                    "lecture_id": selected_lecture_id,
                                    "student_id": student_id,
                                    "date": selected_date,
                                    "status": bulk_status,
                                    "time": bulk_time.strftime("%H:%M"),
                                    "reason": bulk_reason
                                }
                                
                                # 출결 데이터 업데이트
                                update_attendance(new_attendance)
                            
                            st.success(f"{len(selected_student_ids)}명의 학생 출결 정보가 일괄 처리되었습니다.")
                            st.rerun()
                    
                    # 출결 현황 요약
                    st.subheader("📊 출결 현황 요약")
                    
                    # 처리된 출결 수
                    processed_count = len(attendance_data)
                    total_count = len(enrolled_students)
                    remaining_count = total_count - processed_count
                    
                    # 출결 상태별 통계
                    status_counts = {status: 0 for status in ATTENDANCE_STATUS}
                    for a in attendance_data:
                        status_counts[a["status"]] += 1
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("처리 완료", f"{processed_count}/{total_count}", f"{remaining_count}명 미처리")
                    
                    with col2:
                        st.metric("출석", status_counts["출석"])
                    
                    with col3:
                        st.metric("결석", status_counts["결석"])
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("지각", status_counts["지각"])
                    
                    with col2:
                        st.metric("조퇴", status_counts["조퇴"])
                    
                    with col3:
                        st.metric("병가/공결", status_counts["병가"] + status_counts["공결"])
                    
                    # 출결 목록 표시
                    if attendance_data:
                        # 데이터프레임 생성
                        attendance_df = []
                        
                        for a in attendance_data:
                            student = get_student_by_id(a["student_id"])
                            if student:
                                attendance_df.append({
                                    "이름": student["name"],
                                    "학번": student["student_id"],
                                    "학과": student["department"],
                                    "상태": a["status"],
                                    "시간": a.get("time", ""),
                                    "사유": a.get("reason", "")
                                })
                        
                        if attendance_df:
                            st.dataframe(pd.DataFrame(attendance_df), use_container_width=True)
                    
                    # 미처리 학생 목록
                    if remaining_count > 0:
                        st.subheader("⚠️ 미처리 학생 목록")
                        
                        missing_students = []
                        for student in enrolled_students:
                            if student["id"] not in attendance_dict:
                                missing_students.append({
                                    "이름": student["name"],
                                    "학번": student["student_id"],
                                    "학과": student["department"]
                                })
                        
                        if missing_students:
                            st.dataframe(pd.DataFrame(missing_students), use_container_width=True)

# 통계 및 보고서
elif menu == "통계 및 보고서":
    st.title("📊 통계 및 보고서")
    
    tab1, tab2, tab3 = st.tabs(["특강별 통계", "학생별 통계", "보고서 생성"])
    
    # 특강별 통계 탭
    with tab1:
        st.subheader("특강별 출결 통계")
        
        # 특강 선택
        lecture_options = [(l["id"], f"{l['name']} ({l['instructor']})") for l in st.session_state.lectures]
        
        if not lecture_options:
            st.info("등록된 특강이 없습니다. '특강 관리' 메뉴에서 특강을 등록해주세요.")
        else:
            lecture_selection = st.selectbox(
                "특강 선택",
                options=[l[1] for l in lecture_options],
                format_func=lambda x: x,
                key="stats_lecture"
            )
            
            # 선택된 특강 ID 가져오기
            selected_lecture_id = None
            for l_id, l_name in lecture_options:
                if l_name == lecture_selection:
                    selected_lecture_id = l_id
                    break
            
            if selected_lecture_id:
                lecture = get_lecture_by_id(selected_lecture_id)
                
                if lecture:
                    # 특강 정보 표시
                    st.write(f"**특강명:** {lecture['name']}")
                    st.write(f"**강사:** {lecture['instructor']}")
                    st.write(f"**기간:** {lecture['start_date']} ~ {lecture['end_date']}")
                    
                    # 출결 요약 데이터 가져오기
                    summary_df = get_lecture_attendance_summary(selected_lecture_id)
                    
                    if summary_df.empty:
                        st.info("이 특강에 대한 출결 데이터가 없습니다.")
                    else:
                        # 등록 학생 수
                        student_count = len(summary_df)
                        
                        # 출석률 통계
                        attendance_rates = []
                        for _, row in summary_df.iterrows():
                            try:
                                rate = float(row["출석률"].replace("%", ""))
                                attendance_rates.append(rate)
                            except:
                                attendance_rates.append(0)
                        
                        avg_attendance_rate = sum(attendance_rates) / len(attendance_rates) if attendance_rates else 0
                        
                        # 통계 카드
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("등록 학생 수", student_count)
                        
                        with col2:
                            st.metric("평균 출석률", f"{avg_attendance_rate:.1f}%")
                        
                        with col3:
                            # 출석률 90% 이상 학생 수
                            high_attendance = len([r for r in attendance_rates if r >= 90])
                            st.metric("출석률 90% 이상", f"{high_attendance}명", f"{high_attendance/student_count*100:.1f}%")
                        
                        # 출결 상태 분포 그래프
                        st.subheader("출결 상태 분포")
                        
                        status_data = {
                            "상태": ["출석", "지각", "결석", "조퇴", "병가", "공결"],
                            "건수": [
                                summary_df["출석"].sum(),
                                summary_df["지각"].sum(),
                                summary_df["결석"].sum(),
                                summary_df["조퇴"].sum(),
                                summary_df["병가"].sum(),
                                summary_df["공결"].sum()
                            ]
                        }
                        
                        status_df = pd.DataFrame(status_data)
                        
                        # Plotly 바 차트
                        fig = px.bar(
                            status_df,
                            x="상태",
                            y="건수",
                            color="상태",
                            title="출결 상태 분포",
                            color_discrete_map={
                                "출석": "#2ecc71",
                                "지각": "#f1c40f",
                                "결석": "#e74c3c",
                                "조퇴": "#e67e22",
                                "병가": "#3498db",
                                "공결": "#9b59b6"
                            }
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 학생별 출석률 차트
                        st.subheader("학생별 출석률")
                        
                        student_rate_data = []
                        for _, row in summary_df.iterrows():
                            try:
                                rate = float(row["출석률"].replace("%", ""))
                                student_rate_data.append({
                                    "이름": row["이름"],
                                    "학번": row["학번"],
                                    "출석률": rate
                                })
                            except:
                                pass
                        
                        if student_rate_data:
                            # 출석률 기준 정렬
                            student_rate_data.sort(key=lambda x: x["출석률"], reverse=True)
                            student_rate_df = pd.DataFrame(student_rate_data)
                            
                            # Plotly 바 차트
                            fig = px.bar(
                                student_rate_df,
                                y="이름",
                                x="출석률",
                                color="출석률",
                                title="학생별 출석률",
                                labels={"출석률": "출석률 (%)"},
                                color_continuous_scale=["#e74c3c", "#f1c40f", "#2ecc71"],
                                range_color=[0, 100],
                                hover_data=["학번"],
                                orientation="h"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # 날짜별 출석 현황
                        st.subheader("날짜별 출석 현황")
                        
                        # 날짜 컬럼 추출
                        date_columns = [col for col in summary_df.columns if col not in ["학생ID", "이름", "학번", "학과", "출석", "지각", "결석", "조퇴", "병가", "공결", "출석률"]]
                        
                        if date_columns:
                            # 날짜별 상태 카운트
                            date_status_data = []
                            
                            for date in date_columns:
                                status_counts = summary_df[date].value_counts().to_dict()
                                date_data = {"날짜": date}
                                
                                for status in ATTENDANCE_STATUS:
                                    date_data[status] = status_counts.get(status, 0)
                                
                                date_data["미입력"] = status_counts.get("미입력", 0)
                                date_status_data.append(date_data)
                            
                            date_status_df = pd.DataFrame(date_status_data)
                            
                            # 날짜 순으로 정렬
                            date_status_df = date_status_df.sort_values("날짜")
                            
                            # 출석 상태 데이터 준비
                            attendance_data = []
                            for status in ATTENDANCE_STATUS + ["미입력"]:
                                for _, row in date_status_df.iterrows():
                                    attendance_data.append({
                                        "날짜": row["날짜"],
                                        "상태": status,
                                        "인원": row[status]
                                    })
                            
                            attendance_df = pd.DataFrame(attendance_data)
                            
                            # Plotly 스택 바 차트
                            fig = px.bar(
                                attendance_df,
                                x="날짜",
                                y="인원",
                                color="상태",
                                title="날짜별 출결 현황",
                                color_discrete_map={
                                    "출석": "#2ecc71",
                                    "지각": "#f1c40f",
                                    "결석": "#e74c3c",
                                    "조퇴": "#e67e22",
                                    "병가": "#3498db",
                                    "공결": "#9b59b6",
                                    "미입력": "#95a5a6"
                                },
                                barmode="stack"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # 전체 출결 데이터 표시
                        with st.expander("전체 출결 데이터 보기"):
                            st.dataframe(summary_df, use_container_width=True)
    
    # 학생별 통계 탭
    with tab2:
        st.subheader("학생별 출결 통계")
        
        # 학생 검색
        search_query = st.text_input("학생 검색 (이름, 학번)", key="student_stats_search")
        
        # 학생 필터링
        filtered_students = st.session_state.students
        
        if search_query:
            filtered_students = [
                s for s in filtered_students 
                if search_query.lower() in s["name"].lower() or 
                   search_query.lower() in s["student_id"].lower()
            ]
        
        if not filtered_students:
            st.info("검색 조건에 맞는 학생이 없습니다.")
        else:
            # 학생 선택
            student_options = [(s["id"], f"{s['name']} ({s['student_id']})") for s in filtered_students]
            
            student_selection = st.selectbox(
                "학생 선택",
                options=[s[1] for s in student_options],
                format_func=lambda x: x
            )
            
            # 선택된 학생 ID 가져오기
            selected_student_id = None
            for s_id, s_name in student_options:
                if s_name == student_selection:
                    selected_student_id = s_id
                    break
            
            if selected_student_id:
                student = get_student_by_id(selected_student_id)
                
                if student:
                    # 학생 정보 표시
                    st.write(f"**이름:** {student['name']}")
                    st.write(f"**학번:** {student['student_id']}")
                    st.write(f"**학과:** {student['department']}")
                    st.write(f"**학년:** {student['grade']}")
                    
                    # 등록된 특강 목록
                    enrolled_lectures = []
                    if "enrolled_lectures" in student:
                        for lecture_id in student["enrolled_lectures"]:
                            lecture = get_lecture_by_id(lecture_id)
                            if lecture:
                                # 출석률 계산
                                attendance_stats = calculate_attendance_rate(lecture_id, selected_student_id)
                                
                                enrolled_lectures.append({
                                    "id": lecture_id,
                                    "name": lecture["name"],
                                    "instructor": lecture["instructor"],
                                    "period": f"{lecture['start_date']} ~ {lecture['end_date']}",
                                    "status": lecture["status"],
                                    "attendance_rate": attendance_stats["출석률"]
                                })
                    
                    if not enrolled_lectures:
                        st.info("이 학생은 등록된 특강이 없습니다.")
                    else:
                        # 특강별 출석률 차트
                        st.subheader("특강별 출석률")
                        
                        lecture_rate_data = []
                        for lecture in enrolled_lectures:
                            lecture_rate_data.append({
                                "특강명": lecture["name"],
                                "출석률": lecture["attendance_rate"]
                            })
                        
                        lecture_rate_df = pd.DataFrame(lecture_rate_data)
                        
                        # Plotly 바 차트
                        fig = px.bar(
                            lecture_rate_df,
                            y="특강명",
                            x="출석률",
                            color="출석률",
                            title="특강별 출석률",
                            labels={"출석률": "출석률 (%)"},
                            color_continuous_scale=["#e74c3c", "#f1c40f", "#2ecc71"],
                            range_color=[0, 100],
                            orientation="h"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 특강별 출결 현황
                        st.subheader("특강별 출결 현황")
                        
                        # 선택한 특강의 출결 상세 정보
                        for lecture in enrolled_lectures:
                            with st.expander(f"{lecture['name']} ({lecture['period']})"):
                                # 출결 현황 요약
                                attendance_stats = calculate_attendance_rate(lecture["id"], selected_student_id)
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("출석", attendance_stats["출석"])
                                    st.metric("병가", attendance_stats["병가"])
                                
                                with col2:
                                    st.metric("지각", attendance_stats["지각"])
                                    st.metric("공결", attendance_stats["공결"])
                                
                                with col3:
                                    st.metric("결석", attendance_stats["결석"])
                                    st.metric("조퇴", attendance_stats["조퇴"])
                                
                                st.metric("출석률", f"{attendance_stats['출석률']}%")
                                
                                # 출결 상세 기록
                                attendance_records = get_student_attendance(lecture["id"], selected_student_id)
                                
                                if attendance_records:
                                    # 날짜별로 정렬
                                    attendance_records.sort(key=lambda x: x["date"])
                                    
                                    record_data = []
                                    for record in attendance_records:
                                        record_data.append({
                                            "날짜": record["date"],
                                            "상태": record["status"],
                                            "시간": record.get("time", ""),
                                            "사유": record.get("reason", "")
                                        })
                                    
                                    st.dataframe(pd.DataFrame(record_data), use_container_width=True)
                                else:
                                    st.info("이 특강에 대한 출결 기록이 없습니다.")
    
    # 보고서 생성 탭
    with tab3:
        st.subheader("보고서 생성")
        
        report_type = st.radio(
            "보고서 유형",
            options=["특강별 출결 보고서", "학생별 출결 보고서", "종합 출결 현황"]
        )
        
        if report_type == "특강별 출결 보고서":
            # 특강 선택
            lecture_options = [(l["id"], f"{l['name']} ({l['instructor']})") for l in st.session_state.lectures]
            
            if not lecture_options:
                st.info("등록된 특강이 없습니다.")
            else:
                lecture_selection = st.selectbox(
                    "특강 선택",
                    options=[l[1] for l in lecture_options],
                    format_func=lambda x: x,
                    key="report_lecture"
                )
                
                # 선택된 특강 ID 가져오기
                selected_lecture_id = None
                for l_id, l_name in lecture_options:
                    if l_name == lecture_selection:
                        selected_lecture_id = l_id
                        break
                
                if selected_lecture_id:
                    lecture = get_lecture_by_id(selected_lecture_id)
                    
                    if lecture:
                        # 출결 요약 데이터 가져오기
                        summary_df = get_lecture_attendance_summary(selected_lecture_id)
                        
                        if summary_df.empty:
                            st.info("이 특강에 대한 출결 데이터가 없습니다.")
                        else:
                            # 다운로드 옵션
                            file_format = st.radio("파일 형식", ["CSV", "Excel"])
                            
                            # 다운로드 버튼
                            if file_format == "CSV":
                                csv = convert_df_to_csv(summary_df)
                                download_filename = f"{lecture['name']}_출결보고서_{datetime.now().strftime('%Y%m%d')}.csv"
                                
                                st.download_button(
                                    label="CSV 다운로드",
                                    data=csv,
                                    file_name=download_filename,
                                    mime="text/csv"
                                )
                            else:
                                excel = convert_df_to_excel(summary_df)
                                download_filename = f"{lecture['name']}_출결보고서_{datetime.now().strftime('%Y%m%d')}.xlsx"
                                
                                st.download_button(
                                    label="Excel 다운로드",
                                    data=excel,
                                    file_name=download_filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            
                            # 미리보기
                            with st.expander("보고서 미리보기"):
                                st.dataframe(summary_df, use_container_width=True)
        
        elif report_type == "학생별 출결 보고서":
            # 학생 선택
            student_options = [(s["id"], f"{s['name']} ({s['student_id']})") for s in st.session_state.students]
            
            if not student_options:
                st.info("등록된 학생이 없습니다.")
            else:
                student_selection = st.selectbox(
                    "학생 선택",
                    options=[s[1] for s in student_options],
                    format_func=lambda x: x,
                    key="report_student"
                )
                
                # 선택된 학생 ID 가져오기
                selected_student_id = None
                for s_id, s_name in student_options:
                    if s_name == student_selection:
                        selected_student_id = s_id
                        break
                
                if selected_student_id:
                    student = get_student_by_id(selected_student_id)
                    
                    if student:
                        # 학생의 모든 특강 출결 데이터 수집
                        enrolled_lectures = student.get("enrolled_lectures", [])
                        
                        if not enrolled_lectures:
                            st.info("이 학생은 등록된 특강이 없습니다.")
                        else:
                            # 모든 특강의 출결 데이터
                            all_lecture_data = []
                            
                            for lecture_id in enrolled_lectures:
                                lecture = get_lecture_by_id(lecture_id)
                                if lecture:
                                    # 출결 기록
                                    attendance_records = get_student_attendance(lecture_id, selected_student_id)
                                    
                                    # 출결 통계
                                    attendance_stats = calculate_attendance_rate(lecture_id, selected_student_id)
                                    
                                    # 데이터 추가
                                    for record in attendance_records:
                                        all_lecture_data.append({
                                            "특강명": lecture["name"],
                                            "강사": lecture["instructor"],
                                            "날짜": record["date"],
                                            "상태": record["status"],
                                            "시간": record.get("time", ""),
                                            "사유": record.get("reason", "")
                                        })
                            
                            if not all_lecture_data:
                                st.info("이 학생에 대한 출결 데이터가 없습니다.")
                            else:
                                # 데이터프레임 생성
                                student_report_df = pd.DataFrame(all_lecture_data)
                                
                                # 날짜 기준 정렬
                                student_report_df = student_report_df.sort_values("날짜")
                                
                                # 다운로드 옵션
                                file_format = st.radio("파일 형식", ["CSV", "Excel"], key="student_format")
                                
                                # 다운로드 버튼
                                if file_format == "CSV":
                                    csv = convert_df_to_csv(student_report_df)
                                    download_filename = f"{student['name']}_{student['student_id']}_출결보고서_{datetime.now().strftime('%Y%m%d')}.csv"
                                    
                                    st.download_button(
                                        label="CSV 다운로드",
                                        data=csv,
                                        file_name=download_filename,
                                        mime="text/csv"
                                    )
                                else:
                                    excel = convert_df_to_excel(student_report_df)
                                    download_filename = f"{student['name']}_{student['student_id']}_출결보고서_{datetime.now().strftime('%Y%m%d')}.xlsx"
                                    
                                    st.download_button(
                                        label="Excel 다운로드",
                                        data=excel,
                                        file_name=download_filename,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                                
                                # 미리보기
                                with st.expander("보고서 미리보기"):
                                    st.dataframe(student_report_df, use_container_width=True)
        
        elif report_type == "종합 출결 현황":
            # 날짜 범위 선택
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("시작일", value=datetime.now() - timedelta(days=30))
            
            with col2:
                end_date = st.date_input("종료일", value=datetime.now())
            
            if start_date > end_date:
                st.error("종료일은 시작일 이후여야 합니다.")
            else:
                # 선택된 날짜 범위의 모든 출결 데이터 수집
                start_str = start_date.strftime("%Y-%m-%d")
                end_str = end_date.strftime("%Y-%m-%d")
                
                all_attendance_data = []
                
                for attendance in st.session_state.attendance:
                    if start_str <= attendance["date"] <= end_str:
                        student = get_student_by_id(attendance["student_id"])
                        lecture = get_lecture_by_id(attendance["lecture_id"])
                        
                        if student and lecture:
                            all_attendance_data.append({
                                "날짜": attendance["date"],
                                "특강명": lecture["name"],
                                "강사": lecture["instructor"],
                                "학생명": student["name"],
                                "학번": student["student_id"],
                                "학과": student["department"],
                                "상태": attendance["status"],
                                "시간": attendance.get("time", ""),
                                "사유": attendance.get("reason", "")
                            })
                
                if not all_attendance_data:
                    st.info("선택한 기간 내의 출결 데이터가 없습니다.")
                else:
                    # 데이터프레임 생성
                    all_attendance_df = pd.DataFrame(all_attendance_data)
                    
                    # 날짜 기준 정렬
                    all_attendance_df = all_attendance_df.sort_values(["날짜", "특강명", "학생명"])
                    
                    # 다운로드 옵션
                    file_format = st.radio("파일 형식", ["CSV", "Excel"], key="all_format")
                    
                    # 다운로드 버튼
                    if file_format == "CSV":
                        csv = convert_df_to_csv(all_attendance_df)
                        download_filename = f"종합출결현황_{start_str}_{end_str}.csv"
                        
                        st.download_button(
                            label="CSV 다운로드",
                            data=csv,
                            file_name=download_filename,
                            mime="text/csv"
                        )
                    else:
                        excel = convert_df_to_excel(all_attendance_df)
                        download_filename = f"종합출결현황_{start_str}_{end_str}.xlsx"
                        
                        st.download_button(
                            label="Excel 다운로드",
                            data=excel,
                            file_name=download_filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    # 미리보기
                    with st.expander("보고서 미리보기"):
                        st.dataframe(all_attendance_df, use_container_width=True)

# 설정
elif menu == "설정":
    st.title("⚙️ 설정")
    
    tab1, tab2 = st.tabs(["데이터 관리", "시스템 정보"])
    
    # 데이터 관리 탭
    with tab1:
        st.subheader("데이터 백업 및 복원")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**데이터 백업**")
            
            # 백업 파일 생성
            backup_data = {
                "lectures": st.session_state.lectures,
                "students": st.session_state.students,
                "attendance": st.session_state.attendance
            }
            
            # JSON 백업
            json_backup = json.dumps(backup_data, ensure_ascii=False, indent=4)
            backup_filename = f"특강출결관리_백업_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            st.download_button(
                label="데이터 백업 다운로드",
                data=json_backup,
                file_name=backup_filename,
                mime="application/json"
            )
        
        with col2:
            st.write("**데이터 복원**")
            
            # 백업 파일 업로드
            uploaded_file = st.file_uploader("백업 파일 업로드", type=["json"])
            
            if uploaded_file is not None:
                try:
                    backup_data = json.loads(uploaded_file.getvalue().decode("utf-8"))
                    
                    # 필수 키 확인
                    if "lectures" not in backup_data or "students" not in backup_data or "attendance" not in backup_data:
                        st.error("잘못된 백업 파일 형식입니다.")
                    else:
                        # 복원 버튼
                        if st.button("데이터 복원"):
                            # 백업 데이터로 세션 상태 업데이트
                            st.session_state.lectures = backup_data["lectures"]
                            st.session_state.students = backup_data["students"]
                            st.session_state.attendance = backup_data["attendance"]
                            
                            save_data()
                            st.success("데이터가 성공적으로 복원되었습니다.")
                            st.rerun()
                
                except Exception as e:
                    st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        
        st.subheader("⚠️ 데이터 초기화")
        st.warning("데이터 초기화는 모든 특강, 학생, 출결 데이터를 삭제합니다. 이 작업은 되돌릴 수 없습니다.")
        
        if st.button("데이터 초기화"):
            confirm = st.text_input("정말로 모든 데이터를 초기화하시겠습니까? 초기화하려면 'DELETE'를 입력하세요.")
            
            if confirm == "DELETE":
                # 모든 데이터 초기화
                st.session_state.lectures = []
                st.session_state.students = []
                st.session_state.attendance = []
                
                save_data()
                st.success("모든 데이터가 초기화되었습니다.")
                st.rerun()
    
    # 시스템 정보 탭
    with tab2:
        st.subheader("시스템 정보")
        
        st.write("**특강 프로그램 출결 관리 시스템**")
        st.write("Version 1.0.0")
        st.write("Powered by Streamlit")
        
        # 데이터 통계
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("등록된 특강 수", len(st.session_state.lectures))
        
        with col2:
            st.metric("등록된 학생 수", len(st.session_state.students))
        
        with col3:
            st.metric("출결 기록 수", len(st.session_state.attendance))
        
        # 시스템 정보
        st.write("**개발 정보**")
        st.write("- 개발 언어: Python")
        st.write("- 프레임워크: Streamlit")
        st.write("- 데이터 저장소: JSON 파일")
        
        # 라이브러리 버전
        st.write("**라이브러리 버전**")
        st.code("""
        streamlit==1.22.0
        pandas==1.5.3
        numpy==1.24.3
        matplotlib==3.7.1
        plotly==5.14.1
        """)

# 푸터
st.markdown("---")
st.caption("© 2025 특강 프로그램 출결 관리 시스템 | Powered by Streamlit")
                                         
                                         
