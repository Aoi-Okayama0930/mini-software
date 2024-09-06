from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
from pathlib import Path
import shutil
import os

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI()

# テンプレートディレクトリの指定
templates = Jinja2Templates(directory="./templates/")

# データベースファイルの名前とパスの設定
DB_NAME = "library.db"
DATABASE_PATH = Path(DB_NAME)

# 書籍の表紙画像を保存するディレクトリ
UPLOAD_FOLDER = "./static/uploads/"
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# 静的ファイルのルートを追加
app.mount("/static", StaticFiles(directory="static"), name="static")

# データベースの初期化関数
def init_db():
    # データベースに接続
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    # booksテーブルを作成 (存在しない場合のみ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT NOT NULL,
                keywords TEXT,
                cover_image TEXT
        )
    ''')
    # keywordsテーブルを作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL UNIQUE
            )
    ''')
    connection.commit()
    connection.close()

@app.on_event("startup")
async def startup():
    init_db()

# ホームページを表示するエンドポイント
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        books = cursor.execute('SELECT * FROM books').fetchall()
    return templates.TemplateResponse("home.html", {"request": request, "books": books})

# 書籍追加ページを表示するエンドポイント
@app.get("/add_book", response_class=HTMLResponse)
async def add_book(request: Request):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        keywords = cursor.execute('SELECT keyword FROM keywords').fetchall()
    return templates.TemplateResponse("add_book.html", {"request": request, "keywords": keywords})

# All booksページのルート設定
@app.get("/all_books", response_class=HTMLResponse)
async def all_books(request: Request):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        books = cursor.execute('SELECT * FROM books').fetchall()
    return templates.TemplateResponse("all_books.html", {"request": request, "books": books})

# 新しい書籍を追加するエンドポイント
@app.post("/addBook")
async def addBook(request: Request, title: str = Form(...), author: str = Form(...), isbn: str = Form(...), 
                  keywords: str = Form(""), cover_image: UploadFile = File(None)):
    cover_image_filename = None

    if cover_image and cover_image.filename != "":
        cover_image_filename = cover_image.filename
        cover_image_path = os.path.join(UPLOAD_FOLDER, cover_image_filename)
        with open(cover_image_path, "wb") as buffer:
            shutil.copyfileobj(cover_image.file, buffer)
    
    # 書籍情報をデータベースに保存
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO books (title, author, isbn, keywords, cover_image) 
            VALUES (?, ?, ?, ?, ?)
        ''', (title, author, isbn, keywords if keywords else None, cover_image_filename))
        
        if keywords:
            for keyword in keywords.split(','):
                try:
                    cursor.execute('''
                        INSERT INTO keywords (keyword) 
                        VALUES (?)
                    ''', (keyword.strip(),))
                except sqlite3.IntegrityError:
                    pass

        conn.commit()

    return RedirectResponse(url='/', status_code=303)

# 図書リストを表示するエンドポイント
@app.get('/showLibrary', response_class=HTMLResponse)
async def showLibrary(request: Request, search_keyword: str = None):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if search_keyword:
            books = cursor.execute('SELECT * FROM books WHERE keywords LIKE ?', ('%' + search_keyword + '%',)).fetchall()
        else:
            books = cursor.execute('SELECT * FROM books').fetchall()
    return templates.TemplateResponse('libraryList.html', {"request": request, "books": books, "search_keyword": search_keyword})
