import math
import os
import smtplib
import sys
import zipfile
from datetime import datetime
from datetime import date

from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, \
    login_required, logout_user
from imbox import Imbox
from werkzeug.security import check_password_hash, generate_password_hash

from analyzer import parse_db
from cost_adds import cat_list, cat_place


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'KLn|K6ef|?[0Fk"L_c<9%Oi`!WzbR[`X|o#t4dk-b=f8i0Gh)0'
manager = LoginManager(app)
db = SQLAlchemy(app)


class Product(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    article = db.Column(db.Integer, nullable=False)
    cat = db.Column(db.String(50), nullable=False)
    sub_cat = db.Column(db.String(50))
    sub_sub_cat = db.Column(db.String(50))
    title = db.Column(db.String(200), nullable=False)
    guarant = db.Column(db.Integer)
    status = db.Column(db.String(50))
    price = db.Column(db.Integer)
    date_time = db.Column(db.String(50))
    delivery = db.Column(db.String(50))
    items = db.relationship('Cart', backref='product')

    def __init__(self, article, cat, sub_cat, sub_sub_cat, title, guarant,
                 status, price, date_time, delivery,):
        self.article = article
        self.cat = cat
        self.sub_cat = sub_cat
        self.sub_sub_cat = sub_sub_cat
        self.title = title
        self.guarant = guarant
        self.status = status
        self.price = price
        self.date_time = date_time
        self.delivery = delivery

    def __repr__(self):
        return self.title


class Cart(db.Model):

    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.String(50), nullable=False, default='admin')
    id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    item_count = db.Column(db.Integer, nullable=False, default=1)
    cart_id = db.Column(db.Integer)

    def __init__(self, id, item_count):
        self.id = id
        self.item_count = item_count


class Order(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    date_time = db.Column(db.DateTime, nullable=False)
    comment = db.Column(db.String(200), nullable=False)
    item = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50))
    delivery = db.Column(db.Integer)

    def __init__(self, order_id, date_time, comment,
                 item, count, status, delivery):
        self.order_id = order_id
        self.date_time = date_time
        self.comment = comment
        self.item = item
        self.count = count
        self.status = status
        self.delivery = delivery

    def __repr__(self):
        return self.order_id


class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)


class SellProduct(Product):

    def __init__(self, sell_price, item_count, place, total_price,
                 sell_of_one, sell_all):
        self.sell_price = sell_price
        self.item_count = item_count
        self.place = place
        self.total_price = total_price
        self.sell_of_one = sell_of_one
        self.sell_all = sell_all



def sendEMail(text):
    email = "pyscript@yandex.ru"
    dst_email = 'drag817@yandex.ru'
    subject = ('Отчет об обновлении за ' + str(date.today()))
    body = text
    server = smtplib.SMTP("smtp.yandex.ru", 587)
    server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.login("pyscript@yandex.ru", "qiukerydfdcgseih")
    message = 'From: %s\nTo: %s\nSubject: %s\n\n%s' % (
        email, dst_email, subject, body
    )
    server.sendmail(
        "pyscript@yandex.ru", "drag817@yandex.ru", message.encode('utf-8')
    )
    server.quit()


def sell_price():
    # TODO: rename this func
    for prod in PRODUCTS:
        prod.sell_price = prod.price * cat_list[prod.cat]
        sub_cat_list = [
            'Периферийное оборудование',
            'Оргтехника и расходные материалы',
            'Портативные компьютеры'
        ]
        if prod.cat in sub_cat_list:
            try:
                prod.place = cat_place[prod.cat][prod.sub_cat]
            except:
                # TODO: cath except
                prod.place = cat_place[prod.cat]['Остальное']
        else:
            prod.place = cat_place[prod.cat]

    return PRODUCTS


def prepare_catalog(data):
    cat = []
    sub_cat = []

    for prod in PRODUCTS:
        if prod.cat not in cat:
            cat.append(prod.cat)

    for el in cat:
        for prod in PRODUCTS:
            if prod.cat == el:
                if prod.sub_cat not in sub_cat:
                    sub_cat.append(prod.sub_cat)

        foo = {el: sub_cat}
        data.update(foo)
        sub_cat = []

    return data


def restart_server():
    os.execl(sys.executable, 'python', __file__, *sys.argv[1:])


PRODUCTS = Product.query.all()
sell_price()
catalog = {}
cat_log = prepare_catalog(catalog)


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        flash('Для доступа к этой странице необходимо пройти авторизацию!')
        return redirect(url_for('index'))
    if response.status_code == 404:
        flash('Страница не найдена')
        return redirect(url_for('index'))

    return response


@app.route('/')
def index():
    # TODO: add multiple_adding func
    # data = PRODUCTS[:-6:-1]
    return render_template('index.html')


@app.route('/engine', methods=['POST', 'GET'])
@login_required
def engine():
    # TODO: format time in report for normal template
    if request.method == 'POST':
        report = []
        time = datetime.now()
        print('START', (datetime.now() - time))
        report.append('START ' + str(datetime.now() - time))

        # Imbox - Python IMAP for Humans
        with Imbox('imap.yandex.com',
                   username='pyscript',
                   password='qiukerydfdcgseih',
                   ssl=True,
                   ssl_context=None,
                   starttls=False) as imbox:
            inbox_messages = imbox.messages(date__on=date.today())
            print(inbox_messages)
            report.append(str(inbox_messages))

            for uid, message in inbox_messages[::-1]:
                r = message.attachments[0]['content']
                print(r)
                with open("new_price1.zip", "wb") as file:
                    file.write(r.read())
                    print('DONE')
                break

        print('Downloaded', (datetime.now() - time))
        report.append('Downloaded ' + str(datetime.now() - time))

        print('Start unzip', (datetime.now() - time))
        report.append('Start unzip ' + str(datetime.now() - time))
        with zipfile.ZipFile("new_price1.zip", "r") as zip_ref:
            zip_ref.extractall(".")

        print('Unzipped', (datetime.now() - time))
        report.append('Unzipped ' + str(datetime.now() - time))

        print('Init RAM and update Base', (datetime.now() - time))
        report.append('Init RAM and update Base ' + str(datetime.now() - time))

        # Объявляю переменные и загружаю ОЗУ
        old_base = Product.query.all()
        new_base = parse_db()
        old_art_list = []
        new_art_list = []
        upd_count = 0
        add_count = 0
        del_count = 0

        # Вывод количества элементов
        print(len(new_base), 'записей в прайсе')
        print(len(old_base), 'записей в БД')
        report.append(str(len(new_base)) + ' записей в прайсе')
        report.append(str(len(old_base)) + ' записей в БД')

        # Создание списков артикулов для ускорения индексации
        for el in old_base:
            old_art_list.append(el.article)

        for el in new_base:
            new_art_list.append(int(el[0]))

        print('Start update', (datetime.now() - time))
        report.append('Start update ' + str(datetime.now() - time))

        # Обновление БД (в ОЗУ) из прайса
        for prod in old_base:
            if prod.article in new_art_list:
                index = new_art_list.index(prod.article)
                prod.status = new_base[index][6]
                prod.price = new_base[index][7]
                prod.date_time = new_base[index][8]
                prod.delivery = new_base[index][9]
                db.session.add(prod)
                upd_count += 1

        print('UPD finished', upd_count, (datetime.now() - time))
        report.append(
            'UPD finished ' + str(upd_count) + ' ' + str(datetime.now() - time)
        )

        # Если элемента в БД нет, создаю его
        for element in new_base:
            if int(element[0]) not in old_art_list:
                prod = Product(
                    article=element[0],
                    cat=element[1],
                    sub_cat=element[2],
                    sub_sub_cat=element[3],
                    title=element[4],
                    guarant=element[5],
                    status=element[6],
                    price=element[7],
                    date_time=element[8],
                    delivery=element[9],
                )
                db.session.add(prod)
                add_count += 1

        print('ADD finished', add_count, (datetime.now() - time))
        report.append(
            'ADD finished ' + str(add_count) + ' ' + str(datetime.now() - time)
        )

        # Если элемента в ПРЙСЕ нет, удаляю его
        for element in old_art_list:
            if element not in new_art_list:
                prod = Product.query.filter_by(article=element).first()
                db.session.delete(prod)
                del_count += 1

        print('DEL finished', del_count, (datetime.now() - time))
        report.append(
            'DEL finished ' + str(del_count) + ' ' + str(datetime.now() - time)
        )

        # Передаю изменения из ОЗУ в БД
        db.session.commit()

        print('Обновлено', upd_count, 'товаров')
        print('Добавлено', add_count, 'товаров')
        print(' Удалено ', del_count, 'товаров')
        report.append('Обновлено ' + str(upd_count) + ' товаров')
        report.append('Добавлено ' + str(add_count) + ' товаров')
        report.append(' Удалено  ' + str(del_count) + ' товаров')

        # Очистка памяти
        del new_base
        del old_base
        del new_art_list
        del old_art_list
        del upd_count
        del add_count
        del del_count
        del time

        report = '\n'.join(report)

        sendEMail(report)

        del report

        restart_server()

        return redirect('/'), PRODUCTS
    else:
        return render_template('engine.html')


@app.route('/search', methods=['POST', 'GET'])
@login_required
def search():
    if request.method == 'POST':
        if request.form['keyword']:
            data = []
            keyword = request.form['keyword']
            if keyword.isdigit():
                for prod in PRODUCTS:
                    if keyword in str(prod.article):
                        data.append(prod)
            else:
                keyword = keyword.lower().split()
                for el in PRODUCTS:
                    if len(keyword) > 1:
                        if keyword[0] in el.title.lower() and keyword[1] in \
                                el.title.lower():
                            data.append(el)
                    else:
                        if keyword[0] in el.title.lower():
                            data.append(el)
            return render_template('search.html', data=data[:20])
        # TODO: make clickable pages
        else:
            id = request.form.get('Add')
            cart = Cart(
                id=id,
                item_count=1,
            )
            db.session.add(cart)
            db.session.commit()
            flash('Товар добавлен в КОРЗИНУ')
            return render_template('search.html')
    else:
        return render_template('search.html')


@app.route('/catalog')
@login_required
def catalog():
    data = cat_log
    return render_template('catalog.html', data=data)


@app.route('/catalog/<cat>')
@login_required
def cat(cat):
    data = []

    for prod in PRODUCTS:
        if prod.cat == cat:
            data.append(prod)

    if request.method == 'POST':
        id = request.form.get('Add')
        cart = Cart(
            id=id,
            item_count=1,
        )
        db.session.add(cart)
        db.session.commit()
        flash('Товар добавлен в КОРЗИНУ')

    sub_cat = []
    for prod in PRODUCTS:
        if prod.cat == cat:
            if prod.sub_cat not in sub_cat:
                sub_cat.append(prod.sub_cat)

    # TODO: make clickable pages
    return render_template('sub_catalog.html',
                           data=data[:20],
                           sub_cat=sub_cat,
                           cat=cat,
                           )


@app.route('/catalog/sub/<sub_cat>', methods=['POST', 'GET'])
@login_required
def show(sub_cat):
    data = []
    for prod in PRODUCTS:
        if prod.sub_cat == sub_cat:
            data.append(prod)
    if request.method == 'POST':
        id = request.form.get('Add')
        cart = Cart(
            id=id,
            item_count=1,
        )
        db.session.add(cart)
        db.session.commit()
        flash('Товар добавлен в КОРЗИНУ')
        # TODO: make clickable pages
    return render_template('show.html', data=data[:20], sub_cat=sub_cat)


@app.route('/report', methods=['POST', 'GET'])
@login_required
def report():
    if request.method == 'POST':
        flash('Сообщение отправлено')
        dst_email = request.form['email']
        subject = request.form['subject']
        body = request.form['body']
        email = "pyscript@yandex.ru"
        server = smtplib.SMTP("smtp.yandex.ru", 587)
        server.set_debuglevel(1)
        server.ehlo()
        server.starttls()
        server.login("pyscript@yandex.ru", "qiukerydfdcgseih")
        message = 'From: %s\nTo: %s\nSubject: %s\n\n%s' % (
            email, dst_email, subject, body
        )
        server.sendmail(email, dst_email, message.encode('utf-8'))
        server.quit()
    return render_template('report.html')


@app.route('/cart', methods=['POST', 'GET'])
@login_required
def cart():
    # TODO: add sell price + delivery
    cart = Cart.query.all()
    data = []

    if request.method == 'POST':
        if request.form.get('Upd'):
            id_upd = request.form.get('Upd')
            count = int(request.form[id_upd])
            prod = Cart.query.get(id_upd)
            prod.item_count = count
            db.session.add(prod)
            db.session.commit()

        elif request.form.get('Del'):
            id_del = request.form.get('Del')
            prod = Cart.query.get(int(id_del))
            db.session.delete(prod)
            db.session.commit()

        elif request.form.get('Save'):
            comment = request.form['comment']
            if not comment:
                comment = datetime.today().strftime("%d/%m/%y %H:%M:%S")
            flash('Заказ сохранен')

            orders = Order.query.all()
            if orders:
                some_id_list = []
                for order in orders:
                    some_id_list.append(order.order_id)
                some_id = max(some_id_list)
            else:
                some_id = 0

            for prod in cart:
                order = Order(
                    order_id=some_id+1,
                    comment=comment,
                    item=prod.id,
                    count=prod.item_count,
                    date_time=datetime.today(),
                    status='test',
                    delivery=None,
                )
                db.session.add(order)
            db.session.commit()

            prods = Cart.query.all()
            for prod in prods:
                db.session.delete(prod)
            db.session.commit()

            return render_template('orders.html')

    for prod in cart:
        item = Product.query.get(prod.id)
        item.item_count = prod.item_count
        item.cart_id = prod.item_id
        data.append(item)

    return render_template('cart.html', data=data)


@app.route('/orders', methods=['POST', 'GET'])
@login_required
def orders():
    if request.method == 'POST':
        if request.form.get('Del'):
            id_del = request.form.get('Del')
            order = Order.query.filter_by(order_id=int(id_del)).all()
            for item in order:
                db.session.delete(item)
            db.session.commit()

    data = []
    orders = Order.query.all()
    main_order = 0
    all_items = []
    items = {}

    for order in orders:
        if order.order_id != main_order:
            data.append(order)
            main_order = order.order_id

    for order in data:
        for item in Order.query.filter_by(order_id=order.order_id):
            # TODO: rewrite func below with .format
            all_items.append(str(
                str(item.count) + ' x ' + str(Product.query.get(item.item))
            ))
        foo = {order.order_id: all_items}
        items.update(foo)
        all_items = []

    return render_template('orders.html', data=data, items=items)


@app.route('/order/<int:id>', methods=['POST', 'GET'])
@login_required
def order(id):
    if request.method == 'POST':
        if request.form.get('Save'):
            flash('Заказ сохранен')
            order = Order.query.filter_by(order_id=id).all()
            for item in order:
                item.delivery = int(request.form.get('delivery'))
                item.comment = request.form.get('comment')
                db.session.add(item)

            db.session.commit()

        if request.form.get('Del'):
            id_del = int(request.form.get('Del'))
            print(id_del)
            print(type(id_del))
            prods = Order.query.filter_by(order_id=id, item=id_del).all()
            for prod in prods:
                print('DONE')
                print(type(prod))
                db.session.delete(prod)
            db.session.commit()

            if request.form.get('Upd'):
                id_upd = request.form.get('Upd')
                count = int(request.form[id_upd])
                prod = Cart.query.get(id_upd)
                prod.item_count = count
                db.session.add(prod)
                db.session.commit()

    order = Order.query.filter_by(order_id=id)
    comment = order[0].comment

    data = []
    places = 0
    all_price = 0
    all_sell_price = 0
    count_changed = False

    for item in order:
        prod = Product.query.get(item.item)
        prod.sell_price = prod.price * cat_list[prod.cat]
        sub_cat_list = [
            'Периферийное оборудование',
            'Оргтехника и расходные материалы',
            'Портативные компьютеры',
        ]
        if prod.cat in sub_cat_list:
            try:
                prod.place = cat_place[prod.cat][prod.sub_cat]
            except:
                prod.place = cat_place[prod.cat]['Остальное']
        else:
            prod.place = cat_place[prod.cat]

        prod.item_count = item.count
        prod.total_price = prod.item_count * prod.price
        places += prod.place * prod.item_count
        all_price += prod.total_price
        data.append(prod)

    places = math.ceil(places)

    if order[0].delivery:
        delivery = order[0].delivery
    else:
        delivery = 615 + (places * 485)

    if request.method == 'POST':
        if request.form.get('Change'):
            places = 0
            all_price = 0
            for item in data:
                prod = Order.query.filter_by(order_id=id, item=item.id).first()
                count = int(request.form.get(str(item.id)))
                if prod.count != count:
                    count_changed = True
                item.item_count = count
                prod.count = count
                item.total_price = item.item_count * item.price
                places += item.place * item.item_count
                all_price += item.total_price
                db.session.add(prod)
            db.session.commit()

            comment = request.form.get('comment')

            places = math.ceil(places)

            if count_changed:
                delivery = 615 + (places * 485)
            else:
                delivery = int(request.form.get('delivery'))

    for prod in data:
        delivery_part = prod.total_price / all_price * 100
        delivery_add = round(delivery / 100 * delivery_part)
        prod.sell_of_one = round(
            prod.sell_price + (delivery_add / prod.item_count), 2
        )
        prod.sell_all = round(prod.sell_of_one * prod.item_count, 2)
        all_sell_price += prod.sell_all

    all_sell_price = round(all_sell_price, 2)

    return render_template('order.html',
                           data=data,
                           all_sell_price=all_sell_price,
                           delivery=delivery,
                           places=places,
                           comment=comment,
                           id=id,
                           )


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    if request.method == 'POST':
        if login and password:
            user = User.query.filter_by(login=login).first()

            if user and check_password_hash(user.password, password):
                login_user(user)

                # next_page = request.args.get('next')
                return render_template('search.html')
            else:
                flash('Логин или пароль неверен')
        else:
            flash('Заполните формы')

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('login')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if request.method == 'POST':
        if not (login or password or password2):
            flash('Заполните все поля')
        elif password != password2:
            flash('Пароли не совпадают')
        else:
            hash_pwd = generate_password_hash(password)
            new_user = User(login=login, password=hash_pwd)
            db.session.add(new_user)
            db.session.commit()

            return render_template('login.html')

    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True, host='192.168.0.123', port=5000)

# TODO: add favicon


# >>> from main import db
# >>> db.create_all()
