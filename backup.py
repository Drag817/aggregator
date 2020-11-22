@app.route('/update', methods=['POST', 'GET'])
def update():
    if request.method == 'POST':
        old_products = Product.query.all()
        time = datetime.now()
        new_base = parse_db()
        old_art_list = []
        new_art_list = []
        upd_count = 0
        add_count = 0
        del_count = 0

        print(len(new_base), 'записей в прайсе')
        print(len(old_products), 'записей в БД')

        for el in old_products:
            old_art_list.append(el.article)

        for element in new_base:
            new_art_list.append(int(element[0]))
            if int(element[0]) in old_art_list:
                prod = Product.query.filter_by(article=int(element[0])).first()
                prod.status = element[6]
                prod.price = element[7]
                prod.date_time = element[8]
                prod.delivery = element[9]
                db.session.add(prod)
                upd_count += 1

            if int(element[0]) not in old_art_list:
                new_product = Product(
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
                db.session.add(new_product)
                add_count += 1

            if (new_base.index(element) % 5000) == 0 and new_base.index(element) != 0:
                db.session.commit()
                db.session.close()
                print('UPD', new_base.index(element), (datetime.now() - time))

        for element in old_art_list:
            if element not in new_art_list:
                prod = Product.query.filter_by(article=element).first()
                db.session.delete(prod)
                del_count += 1

        print('Обновлено', upd_count, 'товаров')
        print('Добавлено', add_count, 'товаров')
        print(' Удалено ', del_count, 'товаров')

        db.session.commit()

        del new_base
        del new_art_list
        del old_products
        del old_art_list
        del upd_count
        del add_count
        del del_count
        del time

        return redirect('/')
    else:
        return render_template('report.html')