import sqlite3  # импорт в программу модуля sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter.ttk import Combobox
from tkinter.messagebox import showerror, showwarning, showinfo


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.sqlite_connection = None
        self.title("Работа с базами данных")
        self.geometry("700x500")
        # self.iconbitmap("database.ico")

        self.button_explore = tk.Button(self, text="Выберите файл", command=self.browseFiles)
        self.button_explore.grid(row=0, column=0, pady=5)

        self.tables_list = Combobox(self, values=[])
        self.tables_list.grid(row=0, column=2, pady=5)

        self.tables_list.bind("<<ComboboxSelected>>", self.table_update)

        self.tree = ttk.Treeview(self, columns=('1', '2', '3'), show="headings")
        self.tree.grid(row=1, column=0, columnspan=3, sticky="wens")

        # добавляем горизонтальную прокрутку
        scrollbar = ttk.Scrollbar(orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=0, columnspan=3, sticky="we")

        self.button_add = tk.Button(self, text="Добавить запись", command=self.add_record)
        self.button_add.grid(row=3, column=0, pady=5)

        self.button_update = tk.Button(self, text="Обновить запись", command=self.update_record)
        self.button_update.grid(row=3, column=1, pady=5)

        self.button_delete = tk.Button(self, text="Удалить запись", command=self.delete_record)
        self.button_delete.grid(row=3, column=2, pady=5)

        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=1)
        tk.Grid.columnconfigure(self, 2, weight=1)

        tk.Grid.rowconfigure(self, 1, weight=1)

        self.mainloop()

    def browseFiles(self):
        # инициируем выбор файла
        self.filename = filedialog.askopenfilename(initialdir="/",
                                                   title="Выбор файла",
                                                   filetypes=(("Database File", "*.db*"),))

        # создаем подключение к БД
        self.sqlite_connection = self.connect_to_database()
        self.cursor = self.sqlite_connection.cursor()

        # получаем названия таблиц
        self.cursor.execute('''SELECT name
                            FROM sqlite_master
                            WHERE type="table";''')
        result = self.cursor.fetchall()

        # заполняем выпадающий список
        self.tables_list_values = [table_name[0] for table_name in result]
        self.tables_list.config(values=self.tables_list_values)
        self.tables_list.current(0)
        self.table_update("<<ComboboxSelected>>")

    def connect_to_database(self):
        try:
            sqlite_connection = sqlite3.connect(f"{self.filename}")
            print("База данных создана и успешно подключена к SQLite")
            return sqlite_connection
        except sqlite3.Error as error:
            print("Ошибка при подключении к sqlite", error)

    def table_update(self, event):
        self.selected_table = self.tables_list.get()

        # получаем названия заголовков таблицы
        self.cursor.execute(f'''SELECT name
                                FROM PRAGMA_TABLE_INFO('{self.selected_table}');''')
        result = self.cursor.fetchall()

        # заполняем заголовки в нашей таблице
        self.columns = [column_name[0] for column_name in result]
        self.tree.config(columns=self.columns)

        for column_name in result:
            self.tree.heading(column_name, text=column_name)

        # очищаем нашу таблицу ото всех записей
        self.tree.delete(*self.tree.get_children())

        # получаем все записи из таблицы
        self.cursor.execute(f'''SELECT * FROM '{self.selected_table}';''')
        result = self.cursor.fetchall()

        # заполняем нашу таблицу новыми данными
        for row in result:
            self.tree.insert("", tk.END, values=row)

    def add_record(self):
        if self.sqlite_connection is not None:
            # создаем окно для добавления новой записи в текущую таблицу
            self.win_new_record = tk.Tk()
            self.win_new_record.title("Добавить запись")
            self.win_new_record.geometry("400x400")
            # self.win_new_record.iconbitmap("database.ico")

            self.i_row = 0
            self.fields = []

            for table_name in self.columns:
                if table_name != "id":
                    new_label = tk.Label(self.win_new_record, text=f"{table_name}")
                    new_entry = tk.Entry(self.win_new_record)

                    new_label.grid(row=self.i_row, column=0)
                    new_entry.grid(row=self.i_row, column=1)

                    # tk.Grid.rowconfigure(win_new_record, self.i_row, weight=1)

                    self.fields.append(new_entry)

                    self.i_row += 1

            tk.Button(self.win_new_record, text="Добавить", command=self.save_new_record).grid(row=self.i_row, pady=10,
                                                                                               padx=20, column=0,
                                                                                               columnspan=2, sticky="we")

            tk.Grid.columnconfigure(self.win_new_record, 0, weight=1)
            tk.Grid.columnconfigure(self.win_new_record, 1, weight=1)

            self.win_new_record.mainloop()
        else:
            showerror("Ошибка", "Подключение к базе данных отсутствует")

    def save_new_record(self):
        # получаем записи из полей ввода, формируем из них список
        values = [field.get() for field in self.fields]

        # первичный ключ вручную не заполняем
        if self.columns[0] == "id":
            self.columns.pop(0)

        # формируем запрос на добавление новой записи в нашу таблицу
        insert_record = f'''INSERT INTO {self.selected_table} {f"({', '.join(self.columns)})"}
                        VALUES {f"({str(values)[1:-1]})"};'''

        self.cursor.execute(insert_record)
        self.sqlite_connection.commit()
        self.table_update("<<ComboboxSelected>>")
        self.win_new_record.destroy()
        showinfo("Готово", "Запись добавлена")

    def update_record(self):
        if self.sqlite_connection is not None:
            self.win_update_record = tk.Tk()
            self.win_update_record.title("Обновить запись")
            self.win_update_record.geometry("400x400")
            # self.win_update_record.iconbitmap("database.ico")

            select_id = f"SELECT {self.columns[0]} from {self.selected_table}"
            self.cursor.execute(select_id)
            ids = [id[0] for id in self.cursor.fetchall()]

            self.id_label = tk.Label(self.win_update_record, text=f"{self.columns[0]}")
            self.id_list = ttk.Combobox(self.win_update_record, values=ids)

            self.id_label.grid(row=0, column=0)
            self.id_list.grid(row=0, column=1)

            self.i_row = 1
            self.fields = {}

            for table_name in self.columns[1:]:
                new_label = tk.Label(self.win_update_record, text=f"{table_name}")
                new_entry = tk.Entry(self.win_update_record)

                new_label.grid(row=self.i_row, column=0)
                new_entry.grid(row=self.i_row, column=1)

                # tk.Grid.rowconfigure(win_new_record, self.i_row, weight=1)

                self.fields[new_entry] = new_label["text"]

                self.i_row += 1

            tk.Button(self.win_update_record, text="Обновить", command=self.save_update_record).grid(row=self.i_row,
                                                                                                     pady=10, padx=20,
                                                                                                     column=0,
                                                                                                     columnspan=2,
                                                                                                     sticky="we")
            self.id_list.bind("<<ComboboxSelected>>", self.fill_fields)
            self.id_list.current(0)
            self.fill_fields("<<ComboboxSelected>>")

            tk.Grid.columnconfigure(self.win_update_record, 0, weight=1)
            tk.Grid.columnconfigure(self.win_update_record, 1, weight=1)

            self.win_update_record.mainloop()
        else:
            showerror("Ошибка", "Подключение к базе данных отсутствует")

    def fill_fields(self, event):
        # получаем запись (строку) из таблицы по указанному id
        select_record = f'''SELECT * FROM {self.selected_table} 
                        WHERE {self.columns[0]} = "{self.id_list.get()}"'''
        self.cursor.execute(select_record)
        self.values = self.cursor.fetchall()[0][1:]

        # заполняем поля в окне полученными значениями
        for field, value in zip(self.fields, self.values):
            field.delete(0, tk.END)
            if value == None:
                value = "-"
            field.insert(0, value)

    def save_update_record(self):
        # получаем значения всех полей
        actual_values = {field: field.get() for field in self.fields}
        different_values = []
        for value, actual_value in zip(self.values, actual_values.items()):
            # сравниваем изначальные значения с текущими
            if str(value) != actual_value[1]:
                # различающиеся значения записываем в список
                different_values.append(actual_value[0])

        # обновляем значения в базе данных
        for column in different_values:
            update_table = f'''UPDATE {self.selected_table}
                            SET {self.fields[column]} = '{column.get()}'
                            WHERE {self.columns[0]} = "{self.id_list.get()}"'''

            self.cursor.execute(update_table)
            self.sqlite_connection.commit()

        # self.cursor.execute(f'SELECT * FROM {self.selected_table} WHERE id = {self.id_list.get()}')
        # print(self.cursor.fetchall())

        self.table_update("<<ComboboxSelected>>")
        self.win_update_record.destroy()
        showinfo("Готово", "Запись обновлена")

    def delete_record(self):
        if self.sqlite_connection is not None:
            self.win_delete_record = tk.Tk()
            self.win_delete_record.title("Удалить запись")
            self.win_delete_record.geometry("200x150")
            # self.win_delete_record.iconbitmap("database.ico")

            select_id = f"SELECT {self.columns[0]} from {self.selected_table}"
            self.cursor.execute(select_id)
            ids = [id[0] for id in self.cursor.fetchall()]

            self.id_label = tk.Label(self.win_delete_record, text=f"{self.columns[0]}")
            self.id_list = ttk.Combobox(self.win_delete_record, values=ids)

            self.id_label.grid(row=0, column=0)
            self.id_list.grid(row=0, column=1)

            tk.Button(self.win_delete_record, text="Удалить", command=self.save_delete_record).grid(row=1, pady=10,
                                                                                                    padx=20, column=0,
                                                                                                    columnspan=2,
                                                                                                    sticky="we")
            self.id_list.current(0)

            tk.Grid.columnconfigure(self.win_delete_record, 0, weight=1)
            tk.Grid.columnconfigure(self.win_delete_record, 1, weight=1)

            self.win_delete_record.mainloop()
        else:
            showerror("Ошибка", "Подключение к базе данных отсутствует")

    def save_delete_record(self):
        delete_record = f'''DELETE FROM {self.selected_table} 
                        WHERE {self.columns[0]} = "{self.id_list.get()}"'''
        self.cursor.execute(delete_record)
        self.sqlite_connection.commit()
        self.table_update("<<ComboboxSelected>>")
        self.win_delete_record.destroy()
        showinfo("Готово", "Запись удалена")


if __name__ == "__main__":
    app = App()
