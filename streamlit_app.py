import streamlit as st
import numpy as np
import random
import time

# --- 게임 설정 ---
# 게임 보드(판)의 크기를 정의합니다.
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# 테트리스 블록(테트로미노) 모양과 색상을 정의합니다.
SHAPES = {
    'I': ([[1, 1, 1, 1]], (0, 170, 170)),
    'O': ([[1, 1], [1, 1]], (255, 255, 0)),
    'T': ([[0, 1, 0], [1, 1, 1]], (170, 0, 170)),
    'S': ([[0, 1, 1], [1, 1, 0]], (0, 255, 0)),
    'Z': ([[1, 1, 0], [0, 1, 1]], (255, 0, 0)),
    'J': ([[1, 0, 0], [1, 1, 1]], (0, 0, 255)),
    'L': ([[0, 0, 1], [1, 1, 1]], (255, 165, 0))
}

# --- Streamlit 세션 상태 초기화 ---
# st.session_state를 사용하여 게임 상태를 앱 실행 중에 계속 유지합니다.
def initialize_game():
    """새 게임이 시작될 때 호출되는 함수"""
    if 'board' not in st.session_state:
        # 게임 보드를 0으로 채워진 2차원 배열로 생성합니다.
        st.session_state.board = np.zeros((BOARD_HEIGHT, BOARD_WIDTH), dtype=int)
        # 게임 오버 상태를 관리합니다.
        st.session_state.game_over = False
        # 플레이어의 점수를 저장합니다.
        st.session_state.score = 0
        # 현재 움직이는 블록의 정보를 저장합니다.
        st.session_state.current_piece = None
        # 다음에 나올 블록 정보를 저장합니다.
        st.session_state.next_piece_shape = random.choice(list(SHAPES.keys()))
        # 게임 자동 진행을 위한 상태 (True이면 블록이 자동으로 내려감)
        st.session_state.running = False
        # 새로운 블록을 생성합니다.
        new_piece()

def new_piece():
    """새로운 테트리스 블록을 생성하는 함수"""
    # 다음 블록을 현재 블록으로 설정
    shape_key = st.session_state.next_piece_shape
    shape, color = SHAPES[shape_key]
    
    st.session_state.current_piece = {
        'shape': np.array(shape),
        'color_key': shape_key,  # 색상 참조를 위해 키 저장
        'x': BOARD_WIDTH // 2 - len(shape[0]) // 2, # x좌표 (가운데 시작)
        'y': 0 # y좌표 (맨 위 시작)
    }
    
    # 다음에 나올 블록을 무작위로 다시 선택
    st.session_state.next_piece_shape = random.choice(list(SHAPES.keys()))

    # 새 블록이 생성되자마자 다른 블록과 겹치면 게임 오버 처리
    if not is_valid_position(st.session_state.current_piece['shape'], 
                             (st.session_state.current_piece['x'], st.session_state.current_piece['y'])):
        st.session_state.game_over = True
        st.session_state.running = False


# --- 게임 로직 함수 ---
def is_valid_position(shape, pos, board=None):
    """블록이 현재 위치에 있을 수 있는지 확인하는 함수"""
    if board is None:
        board = st.session_state.board
    
    piece_height, piece_width = shape.shape
    x, y = pos

    for r in range(piece_height):
        for c in range(piece_width):
            if shape[r, c]: # 블록의 채워진 부분만 검사
                board_y = y + r
                board_x = x + c
                # 보드 경계를 벗어나는지 확인
                if not (0 <= board_x < BOARD_WIDTH and 0 <= board_y < BOARD_HEIGHT):
                    return False
                # 다른 블록과 겹치는지 확인
                if board[board_y, board_x]:
                    return False
    return True

def lock_piece():
    """블록을 보드에 고정시키는 함수"""
    shape = st.session_state.current_piece['shape']
    x = st.session_state.current_piece['x']
    y = st.session_state.current_piece['y']
    shape_key = st.session_state.current_piece['color_key']

    for r in range(shape.shape[0]):
        for c in range(shape.shape[1]):
            if shape[r, c]:
                # 블록이 있는 위치를 SHAPES 딕셔너리의 인덱스(1부터)로 표시
                st.session_state.board[y + r, x + c] = list(SHAPES.keys()).index(shape_key) + 1
    
    # 줄이 꽉 찼는지 확인하고 제거
    clear_lines()
    # 새 블록 생성
    new_piece()


def clear_lines():
    """꽉 찬 줄을 찾아 제거하고 점수를 추가하는 함수"""
    lines_cleared = 0
    new_board = [row for row in st.session_state.board if not np.all(row)]
    lines_cleared = BOARD_HEIGHT - len(new_board)
    
    if lines_cleared > 0:
        # 제거된 줄만큼 맨 위에 새로운 빈 줄을 추가
        st.session_state.board = np.vstack([np.zeros((lines_cleared, BOARD_WIDTH), dtype=int), np.array(new_board)])
        # 점수 계산 (제거한 줄 수에 따라 점수 차등 지급)
        st.session_state.score += lines_cleared * 100 * lines_cleared 

def move_piece(dx, dy):
    """블록을 좌우 또는 아래로 이동시키는 함수"""
    if st.session_state.game_over:
        return

    new_x = st.session_state.current_piece['x'] + dx
    new_y = st.session_state.current_piece['y'] + dy
    
    if is_valid_position(st.session_state.current_piece['shape'], (new_x, new_y)):
        st.session_state.current_piece['x'] = new_x
        st.session_state.current_piece['y'] = new_y
    elif dy > 0: # 아래로 이동 중 충돌한 경우
        lock_piece()

def rotate_piece():
    """블록을 시계 방향으로 회전시키는 함수"""
    if st.session_state.game_over:
        return

    # np.rot90 함수를 사용하여 배열을 90도 회전
    rotated_shape = np.rot90(st.session_state.current_piece['shape'])
    if is_valid_position(rotated_shape, (st.session_state.current_piece['x'], st.session_state.current_piece['y'])):
        st.session_state.current_piece['shape'] = rotated_shape

def drop_piece():
    """블록을 한번에 맨 아래로 내리는 함수"""
    if st.session_state.game_over:
        return
    
    y = st.session_state.current_piece['y']
    # 더 이상 내려갈 수 없을 때까지 y좌표를 증가
    while is_valid_position(st.session_state.current_piece['shape'], (st.session_state.current_piece['x'], y + 1)):
        y += 1
    st.session_state.current_piece['y'] = y
    lock_piece()


# --- UI 렌더링 함수 ---
def draw_board():
    """게임 보드와 블록을 화면에 그리는 함수"""
    # 현재 보드 상태를 복사하여, 움직이는 블록을 그 위에 덧그립니다.
    display_board = st.session_state.board.copy()
    
    if st.session_state.current_piece and not st.session_state.game_over:
        shape = st.session_state.current_piece['shape']
        x = st.session_state.current_piece['x']
        y = st.session_state.current_piece['y']
        shape_key = st.session_state.current_piece['color_key']
        
        for r in range(shape.shape[0]):
            for c in range(shape.shape[1]):
                if shape[r, c]:
                    display_board[y + r, x + c] = list(SHAPES.keys()).index(shape_key) + 1

    # HTML과 CSS를 사용하여 보드를 시각적으로 표현합니다.
    cell_size = 25 # 각 셀의 크기 (픽셀)
    board_html = f"<div style='display: grid; grid-template-columns: repeat({BOARD_WIDTH}, {cell_size}px); gap: 1px; border: 2px solid #333; background-color: #000; width: fit-content;'>"
    
    colors = [ (0,0,0) ] + [ SHAPES[key][1] for key in SHAPES ]
    
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            color_val = colors[int(display_board[r, c])]
            board_html += f"<div style='width: {cell_size}px; height: {cell_size}px; background-color: rgb{color_val};'></div>"
    
    board_html += "</div>"
    st.markdown(board_html, unsafe_allow_html=True)


def draw_next_piece():
    """'다음 블록'을 보여주는 UI를 그리는 함수"""
    st.write("**다음 블록**")
    shape_key = st.session_state.next_piece_shape
    shape, color = SHAPES[shape_key]
    
    cell_size = 20
    # 4x4 그리드를 기준으로 표시
    grid_html = f"<div style='display: grid; grid-template-columns: repeat(4, {cell_size}px); gap: 1px; width: fit-content;'>"
    
    shape_np = np.array(shape)
    for r in range(4):
        for c in range(4):
            is_filled = False
            if r < shape_np.shape[0] and c < shape_np.shape[1] and shape_np[r,c]:
                is_filled = True
            
            bg_color = f"rgb{color}" if is_filled else "rgb(240, 242, 246)"
            grid_html += f"<div style='width: {cell_size}px; height: {cell_size}px; background-color: {bg_color};'></div>"
    
    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

# --- 메인 앱 로직 ---
st.set_page_config(page_title="Streamlit 테트리스", layout="centered")

st.title("테트리스")
st.write("Streamlit으로 만든 간단한 테트리스 게임입니다.")

# 게임 상태 초기화 (앱이 처음 실행될 때 한 번만 호출)
if 'board' not in st.session_state:
    initialize_game()

# 게임 화면을 두 개의 컬럼으로 나눔 (왼쪽: 게임 보드, 오른쪽: 정보 및 컨트롤)
col1, col2 = st.columns([2, 1])

with col1:
    # 게임 보드를 그릴 공간
    board_placeholder = st.empty()
    
with col2:
    # 점수, 다음 블록, 게임 시작/정지 버튼 배치
    st.write(f"**점수: {st.session_state.score}**")
    draw_next_piece()
    
    st.write("---")
    st.write("**게임 조작**")
    
    # 게임 시작/일시정지 버튼
    if st.session_state.game_over:
        if st.button("새 게임 시작"):
            # 세션 상태를 초기화하여 새 게임 시작
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            initialize_game()
            st.rerun() # 앱을 새로고침하여 즉시 반영
    else:
        if not st.session_state.running:
            if st.button("게임 시작"):
                st.session_state.running = True
                st.rerun()
        else:
            if st.button("일시정지"):
                st.session_state.running = False
                st.rerun()

    st.write("---")
    st.write("**블록 조작**")
    
    # 블록 조작 버튼
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("← 왼쪽"):
            move_piece(-1, 0)
    with c2:
        if st.button("회전 ↑"):
            rotate_piece()
    with c3:
        if st.button("오른쪽 →"):
            move_piece(1, 0)

    if st.button("↓ 아래로"):
        move_piece(0, 1)

    if st.button("한번에 내리기 (Space)"):
        drop_piece()

# 게임 루프 (자동으로 블록이 내려가는 로직)
if st.session_state.running and not st.session_state.game_over:
    with col1:
        board_placeholder.empty() # 이전 보드 지우기
        draw_board()

        # 0.5초마다 블록을 한 칸씩 아래로 내림
        time.sleep(0.5)
        move_piece(0, 1)
        st.rerun() # 화면을 다시 그려서 변경사항을 반영

elif st.session_state.game_over:
    with col1:
        board_placeholder.empty()
        draw_board()
        st.error("게임 오버!")
else:
    # 게임이 시작되지 않았거나 일시정지 상태일 때
    with col1:
        board_placeholder.empty()
        draw_board()