from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
import sqlite3
from pathlib import Path

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI()

# テンプレートディレクトリの指定
templates = Jinja2Templates(directory="./templates/")

# データベースファイルの名前とパスの設定
DB_NAME = "contacts.db"
DATABASE_PATH = Path(DB_NAME)

# データベースの初期化関数
def init_db():
    # データベースに接続
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    # contactsテーブルを作成 (存在しない場合のみ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            memo TEXT
        )
    ''')
    # 初期データの挿入 (任意)
    cursor.execute('''
        INSERT INTO contacts (name, phone, memo) VALUES
        ('test user', '000-1111-2222', 'あいうえお')
    ''')
    # 変更を保存し、接続を閉じる
    connection.commit()
    connection.close()

# アプリケーションの起動時に実行されるイベントハンドラ
@app.on_event("startup")
async def startup():
    # DB初期化関数の呼び出し
    init_db()

# アプリケーションの終了時に実行されるイベントハンドラ (ここでは何もしない)
@app.on_event("shutdown")
async def shutdown():
    pass

# ホームページを表示するエンドポイント
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # home.html テンプレートをレンダリングして返す
    return templates.TemplateResponse("home.html", {"request": request})

# 新しい連絡先を追加するエンドポイント
@app.post("/addContact")
async def addContact(request: Request,name: str=Form(...), phone: str=Form(...), memo: str=Form(...)):
    # データベースに接続し、新しいレコードを挿入
    with sqlite3.connect(DB_NAME) as conn:
        logging.debug("addRecord")
        cursor = conn.cursor()
        cursor.execute('''
            insert into contacts (name, phone, memo) values
            (?, ?, ?)
        ''', (name, phone, memo))
        conn.commit()
    # ホームページにリダイレクト
    return RedirectResponse(url='/', status_code=303)

# 連絡先リストをリセットするエンドポイント
@app.post("/resetContactList")
async def resetContactList(request: Request):
    # データベースに接続し、contactsテーブルを空にする
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("delete from contacts")
        conn.commit()
    # ホームページにリダイレクト
    return RedirectResponse(url='/', status_code=303)

# 連絡先リストを表示するエンドポイント
@app.get('/showContactList', response_class=HTMLResponse)
async def showContactList(request: Request):
    # データベースに接続し、全てのレコードを取得
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        items = cursor.execute('''
            select * from contacts
        '''
        ).fetchall()
        # テンプレートに渡すパラメータを設定
        param = {'request': request, 'items': items}
    # contactList.html テンプレートをレンダリングして返す
    return templates.TemplateResponse('contactList.html', param)
