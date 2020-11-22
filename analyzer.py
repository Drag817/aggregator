import xlrd2


def init_xlsx():
    with xlrd2.open_workbook("novosibirsk.e2e4online.ru.xlsx") as book:
        return book


def init_sheet(book):
    sh = book.sheet_by_index(0)
    return sh


def xlsx_to_list(sh):
    item = []
    base = []
    for rowx in range(sh.nrows)[12:]:
        for colx in range(sh.ncols):
            str_item = str(sh.cell_value(rowx, colx))
            str_item = str_item.replace('          ', 'cat ')
            item.append(str_item)
        base.append(item)
        item = []
    return base


def base_sort(base):
    new_base = []
    numbers = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')
    for element in base:
        if element[0].count('cat ') == 1:
            element[0] = element[0].replace('cat ', '')
            sub_category = element[0]
            sub_sub_category = ''
            continue
        elif element[0].count('cat ') == 2:
            element[0] = element[0].replace('cat ', '')
            sub_sub_category = element[0]
            continue
        elif element[0].count('cat ') > 2:
            element[0] = element[0].replace('cat ', '')
            sub_sub_category = element[0]
            continue
        elif element[0].startswith(numbers):
            element.insert(1, category)
            element.insert(2, sub_category)
            element.insert(3, sub_sub_category)
            new_base.append(element)
        else:
            category = element[0]
            sub_category = ''
            sub_sub_category = ''
            continue
    return new_base


def parse_db():
    book = init_xlsx()
    sh = init_sheet(book)
    base = xlsx_to_list(sh)
    new_base = base_sort(base)
    del sh
    del base
    return new_base


# @app.route('/create', methods=['POST', 'GET'])
# def create():
#     if request.method == 'POST':
#         new_base = parse_db()
#
#         for element in new_base:
#             product = Product(
#                 article=element[0],
#                 cat=element[1],
#                 sub_cat=element[2],
#                 sub_sub_cat=element[3],
#                 title=element[4],
#                 guarant=element[5],
#                 status=element[6],
#                 price=element[7],
#                 date_time=element[8],
#                 delivery=element[9],
#             )
#             db.session.add(product)
#
#         db.session.commit()
#
#         del new_base
#
#         return redirect('/')
#     else:
#         return render_template('create.html')

