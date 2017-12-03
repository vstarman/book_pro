# -*- coding:utf-8 -*-
from flask import Flask, render_template, request, flash, \
    redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired


import sys
reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
# 数据库链接设置
app.secret_key = 'aasdaswkJYYVUSud'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:meiyoumima920@localhost:3306/book_test'
# 开启修改追踪,会耗性能
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 开启原始sql语句返回
# app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


class AddBookForm(FlaskForm):
    """表单模块"""
    author_name = StringField('作者: ', validators=[InputRequired()])
    book_name = StringField('书名: ', validators=[InputRequired()])
    submit = SubmitField('提交')


class Author(db.Model):
    """作者表"""
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # backref为类Book申明新属性的方法(book.author=书名)
    # lazy为何时查询数据, dynamic指被使用时加载, 会进行过滤,返回对象多时,用此法
    # lazy=subquery, 为立即加载,可以减少总查询量,返回条目多时,则会慢
    books = db.relationship('Book', backref='author', lazy='dynamic')


class Book(db.Model):
    """书籍表"""
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))


@app.route('/delete_author/<int:author_id>')
def delete_author(author_id):
    author = Author.query.get(author_id)
    if author:
        try:
            # delete books
            # Book.query.filter_by(author_id=author.id).delete()
            # delete author
            db.session.delete(author)
            db.session.commit()
        except Exception as e:
            print e
            flash('作者删除失败')
    else:
        flash('该作者不存在')
    return redirect(url_for('index'))


@app.route('/delete/<int:book_id>')
def delete_book(book_id):
    book = Book.query.get(book_id)
    if book:
        # 查到,删除
        # db.session.delete()
        try:
            _del(book)
        except Exception as e:
            print e
            flash('书籍删除失败')
            db.session.rollback()
    else:
        flash('该书不存在')
    return redirect(url_for('index'))


@app.route('/', methods=['post', 'get'])
def index():
    """主页"""
    add_book_form = AddBookForm()

    # 当表单提交时,才会返回True
    if add_book_form.validate_on_submit():
        # 获取数据
        author_name = add_book_form.author_name.data
        book_name = add_book_form.book_name.data
        # 数据校验
        # 看数据库有没有作者
        author = Author.query.filter_by(name=author_name).first()
        if author:
            # 看有无同名书
            book = Book.query.filter_by(name=book_name).first()
            if book:
                flash('已存在同名书籍')
            else:  # 操作数据库时需要捕获异常
                try:
                    # 添加书籍信息
                    book = Book(name=book_name, author_id=author.id)
                    _add(book)
                except Exception as e:
                    print e
                    # 回滚本次事件前
                    db.session.rollback()
                    flash('作者已有该书籍')
        else:
            # 无该作者
            try:
                # 添加作者,和书名
                author = Author(name=author_name)
                _add(author)
                book = Book(name=book_name, author_id=author.id)
                _add(book)
            except Exception as e:
                print e
                db.session.rollback()
                flash('数据添加失败')
        print author_name, book_name
    else:
        if request.method == 'POST':
            flash('输入有误')

    authors = Author.query.all()
    return render_template('book.html', authors=authors, form=add_book_form)


def _add(*args):
    """数据库: 添加,提交"""
    db.session.add_all(args)
    db.session.commit()


def _del(args):
    """数据库:删除"""
    db.session.delete(args)
    db.session.commit()

if __name__ == '__main__':
    """"""
    db.drop_all()
    db.create_all()
    # 生成数据
    au1 = Author(name='老王')
    au2 = Author(name='老尹')
    au3 = Author(name='老刘')
    _add(au1, au2, au3)
    bk1 = Book(name='老王回忆录', author_id=au1.id)
    bk2 = Book(name='我读书少，你别骗我', author_id=au1.id)
    bk3 = Book(name='如何才能让自己更骚', author_id=au2.id)
    bk4 = Book(name='怎样征服美丽少女', author_id=au3.id)
    bk5 = Book(name='如何征服英俊少男', author_id=au3.id)
    _add(bk1, bk2, bk3, bk4, bk5)

    app.run(debug=True)
