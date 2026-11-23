
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from backend import (
    create_user, get_all_users, update_user, delete_user,
    create_table, get_all_tables, update_table, delete_table,
    create_booking, get_all_bookings, update_booking,
    delete_booking, check_table_availability
)

DATE_FORMAT = "%Y-%m-%d %H:%M"


class RestaurantApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("VPc07 — Restaurant Booking")
        self.geometry("1100x720")
        self.minsize(850, 580)

        self.selected_user = None
        self.selected_table = None
        self.selected_booking = None

        self.user_options = {}
        self.table_options = {}
        self.booking_data = {}

        ttk.Label(
            self,
            text="Система бронирования ресторана",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(
            fill="both", expand=True, padx=15, pady=5
        )

        self._build_users_tab()
        self._build_tables_tab()
        self._build_bookings_tab()

        ttk.Button(
            self,
            text="Обновить все данные",
            command=self.refresh
        ).pack(pady=10)

        self.refresh()

    # =====================================
    # ОБЩИЕ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =====================================

    def _make_tree(self, parent, columns):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=10)

        names = [col[0] for col in columns]

        tree = ttk.Treeview(
            frame,
            columns=names,
            show="headings",
            height=10,
            selectmode="browse"
        )

        for key, heading, width in columns:
            tree.heading(key, text=heading)
            tree.column(key, width=width, minwidth=60)

        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return tree

    def _entry(self, parent, label, width=20):
        group = ttk.Frame(parent)
        group.pack(side="left", padx=8, pady=5)

        ttk.Label(group, text=label).pack(anchor="w")

        entry = ttk.Entry(group, width=width)
        entry.pack(pady=4)

        return entry

    def _run_action(self, action, success_message):
        try:
            action()
            self.refresh()
            messagebox.showinfo(
                "Успешно", success_message
            )
        except Exception as error:
            messagebox.showerror(
                "Ошибка", str(error)
            )

    def _get_selected(self, tree):
        selected = tree.selection()
        if not selected:
            return None
        return tree.item(selected[0], "values")

    def _clear_selection(self, tree):
        for item in tree.selection():
            tree.selection_remove(item)

    # =====================================
    # ВКЛАДКА 1 — ПОЛЬЗОВАТЕЛИ
    # =====================================

    def _build_users_tab(self):
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Пользователи")

        self.user_tree = self._make_tree(
            tab,
            [
                ("id", "ID", 70),
                ("name", "Имя", 250),
                ("phone", "Телефон", 200),
            ]
        )

        self.user_tree.bind(
            "<<TreeviewSelect>>", self._select_user
        )

        form = ttk.LabelFrame(
            tab, text="Данные пользователя", padding=10
        )
        form.pack(fill="x")

        self.user_name = self._entry(form, "Имя")
        self.user_phone = self._entry(form, "Телефон")

        buttons = ttk.Frame(tab)
        buttons.pack(pady=12)

        ttk.Button(
            buttons, text="Добавить",
            command=self._add_user
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Изменить",
            command=self._update_user
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Удалить",
            command=self._delete_user
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Очистить",
            command=self._clear_user
        ).pack(side="left", padx=5)

    def _select_user(self, event=None):
        row = self._get_selected(self.user_tree)
        if not row:
            return

        self.selected_user = int(row[0])

        self.user_name.delete(0, tk.END)
        self.user_name.insert(0, row[1])

        self.user_phone.delete(0, tk.END)
        self.user_phone.insert(0, row[2])

    def _clear_user(self):
        self.selected_user = None
        self.user_name.delete(0, tk.END)
        self.user_phone.delete(0, tk.END)
        self._clear_selection(self.user_tree)

    def _add_user(self):
        self._run_action(
            lambda: create_user(
                self.user_name.get(),
                self.user_phone.get()
            ),
            "Пользователь добавлен"
        )

    def _update_user(self):
        if self.selected_user is None:
            messagebox.showwarning(
                "Внимание", "Выберите пользователя"
            )
            return

        self._run_action(
            lambda: update_user(
                self.selected_user,
                self.user_name.get(),
                self.user_phone.get()
            ),
            "Пользователь обновлён"
        )

    def _delete_user(self):
        if self.selected_user is None:
            messagebox.showwarning(
                "Внимание", "Выберите пользователя"
            )
            return

        if messagebox.askyesno(
            "Удаление",
            "Удалить пользователя и все его бронирования?"
        ):
            self._run_action(
                lambda: delete_user(self.selected_user),
                "Пользователь удалён"
            )

    # =====================================
    # ВКЛАДКА 2 — СТОЛЫ
    # =====================================

    def _build_tables_tab(self):
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Столы")

        self.table_tree = self._make_tree(
            tab,
            [
                ("id", "ID", 70),
                ("number", "Номер стола", 200),
                ("seats", "Количество мест", 200),
            ]
        )

        self.table_tree.bind(
            "<<TreeviewSelect>>", self._select_table
        )

        form = ttk.LabelFrame(
            tab, text="Данные стола", padding=10
        )
        form.pack(fill="x")

        self.table_number = self._entry(
            form, "Номер стола"
        )
        self.table_seats = self._entry(
            form, "Количество мест"
        )

        buttons = ttk.Frame(tab)
        buttons.pack(pady=12)

        ttk.Button(
            buttons, text="Добавить",
            command=self._add_table
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Изменить",
            command=self._update_table
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Удалить",
            command=self._delete_table
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Очистить",
            command=self._clear_table
        ).pack(side="left", padx=5)

    def _select_table(self, event=None):
        row = self._get_selected(self.table_tree)
        if not row:
            return

        self.selected_table = int(row[0])

        self.table_number.delete(0, tk.END)
        self.table_number.insert(0, row[1])

        self.table_seats.delete(0, tk.END)
        self.table_seats.insert(0, row[2])

    def _clear_table(self):
        self.selected_table = None
        self.table_number.delete(0, tk.END)
        self.table_seats.delete(0, tk.END)
        self._clear_selection(self.table_tree)

    def _add_table(self):
        self._run_action(
            lambda: create_table(
                int(self.table_number.get()),
                int(self.table_seats.get())
            ),
            "Стол добавлен"
        )

    def _update_table(self):
        if self.selected_table is None:
            messagebox.showwarning(
                "Внимание", "Выберите стол"
            )
            return

        self._run_action(
            lambda: update_table(
                self.selected_table,
                int(self.table_number.get()),
                int(self.table_seats.get())
            ),
            "Данные стола обновлены"
        )

    def _delete_table(self):
        if self.selected_table is None:
            messagebox.showwarning(
                "Внимание", "Выберите стол"
            )
            return

        if messagebox.askyesno(
            "Удаление",
            "Удалить стол и все его бронирования?"
        ):
            self._run_action(
                lambda: delete_table(self.selected_table),
                "Стол удалён"
            )

    # =====================================
    # ВКЛАДКА 3 — БРОНИРОВАНИЯ
    # =====================================

    def _build_bookings_tab(self):
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Бронирования")

        self.booking_tree = self._make_tree(
            tab,
            [
                ("id", "ID", 50),
                ("user", "Пользователь", 140),
                ("table", "Стол", 80),
                ("start", "Начало", 180),
                ("end", "Окончание", 180),
            ]
        )

        self.booking_tree.bind(
            "<<TreeviewSelect>>", self._select_booking
        )

        form = ttk.LabelFrame(
            tab, text="Данные бронирования", padding=10
        )
        form.pack(fill="x")

        row1 = ttk.Frame(form)
        row1.pack(fill="x")

        ttk.Label(
            row1, text="Пользователь:"
        ).pack(side="left", padx=5)

        self.booking_user = ttk.Combobox(
            row1, state="readonly", width=25
        )
        self.booking_user.pack(side="left", padx=8)

        ttk.Label(
            row1, text="Стол:"
        ).pack(side="left", padx=5)

        self.booking_table = ttk.Combobox(
            row1, state="readonly", width=25
        )
        self.booking_table.pack(side="left", padx=8)

        row2 = ttk.Frame(form)
        row2.pack(fill="x", pady=8)

        self.booking_start = self._entry(
            row2, "Начало (ГГГГ-ММ-ДД ЧЧ:ММ)", 22
        )
        self.booking_end = self._entry(
            row2, "Конец (ГГГГ-ММ-ДД ЧЧ:ММ)", 22
        )

        buttons = ttk.Frame(tab)
        buttons.pack(pady=12)

        ttk.Button(
            buttons, text="Проверить доступность",
            command=self._check_availability
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Добавить",
            command=self._add_booking
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Изменить",
            command=self._update_booking
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Удалить",
            command=self._delete_booking
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Очистить",
            command=self._clear_booking
        ).pack(side="left", padx=5)

    def _booking_values(self):
        user_label = self.booking_user.get()
        table_label = self.booking_table.get()

        if user_label not in self.user_options:
            raise ValueError("Выберите пользователя")

        if table_label not in self.table_options:
            raise ValueError("Выберите стол")

        try:
            start = datetime.strptime(
                self.booking_start.get(), DATE_FORMAT
            )
            end = datetime.strptime(
                self.booking_end.get(), DATE_FORMAT
            )
        except ValueError:
            raise ValueError(
                "Введите дату в формате 2026-12-05 19:00"
            )

        if start >= end:
            raise ValueError(
                "Конец бронирования должен быть позже начала"
            )

        return (
            self.user_options[user_label],
            self.table_options[table_label],
            start, end
        )

    def _select_booking(self, event=None):
        row = self._get_selected(self.booking_tree)
        if not row:
            return

        booking_id = int(row[0])
        self.selected_booking = booking_id

        booking = self.booking_data[booking_id]

        for label, user_id in self.user_options.items():
            if user_id == booking["user_id"]:
                self.booking_user.set(label)
                break

        for label, table_id in self.table_options.items():
            if table_id == booking["table_id"]:
                self.booking_table.set(label)
                break

        self.booking_start.delete(0, tk.END)
        self.booking_start.insert(
            0, booking["start_time"].strftime(DATE_FORMAT)
        )

        self.booking_end.delete(0, tk.END)
        self.booking_end.insert(
            0, booking["end_time"].strftime(DATE_FORMAT)
        )

    def _clear_booking(self):
        self.selected_booking = None
        self.booking_user.set("")
        self.booking_table.set("")

        self.booking_start.delete(0, tk.END)
        self.booking_end.delete(0, tk.END)

        tomorrow = (
            datetime.now().replace(
                hour=19, minute=0,
                second=0, microsecond=0
            ) + timedelta(days=1)
        )

        self.booking_start.insert(
            0, tomorrow.strftime(DATE_FORMAT)
        )
        self.booking_end.insert(
            0, (tomorrow + timedelta(hours=2)).strftime(
                DATE_FORMAT
            )
        )

        self._clear_selection(self.booking_tree)

    # =====================================
    # ИСПРАВЛЕННАЯ ПРОВЕРКА ДОСТУПНОСТИ
    # =====================================

    def _check_availability(self):
        try:
            _, table_id, start, end = self._booking_values()

            if self.selected_booking is None:
                # Новое бронирование:
                # проверяем все существующие записи.
                available = check_table_availability(
                    table_id, start, end
                )

            else:
                # Редактирование:
                # получаем актуальные данные из БД
                # и игнорируем собственную бронь.
                bookings = get_all_bookings()

                if not any(
                    b["id"] == self.selected_booking
                    for b in bookings
                ):
                    raise ValueError(
                        "Выбранное бронирование не найдено. "
                        "Обновите данные."
                    )

                # Проверяем, что выбранный стол существует.
                if table_id not in self.table_options.values():
                    raise ValueError("Стол не найден")

                available = True

                for booking in bookings:

                    # Не сравниваем бронь с самой собой.
                    if booking["id"] == self.selected_booking:
                        continue

                    # Другой стол не создаёт конфликт.
                    if booking["table_id"] != table_id:
                        continue

                    # Условие пересечения интервалов.
                    if (
                        booking["start_time"] < end
                        and booking["end_time"] > start
                    ):
                        available = False
                        break

            if available:
                messagebox.showinfo(
                    "Доступность",
                    "Стол свободен на выбранное время!"
                )
            else:
                messagebox.showwarning(
                    "Доступность",
                    "Стол занят! Выберите другое время."
                )

        except Exception as error:
            messagebox.showerror(
                "Ошибка", str(error)
            )

    def _add_booking(self):
        self._run_action(
            lambda: create_booking(
                *self._booking_values()
            ),
            "Бронирование создано"
        )

    def _update_booking(self):
        if self.selected_booking is None:
            messagebox.showwarning(
                "Внимание", "Выберите бронирование"
            )
            return

        self._run_action(
            lambda: update_booking(
                self.selected_booking,
                *self._booking_values()
            ),
            "Бронирование обновлено"
        )

    def _delete_booking(self):
        if self.selected_booking is None:
            messagebox.showwarning(
                "Внимание", "Выберите бронирование"
            )
            return

        if messagebox.askyesno(
            "Удаление",
            "Удалить выбранное бронирование?"
        ):
            self._run_action(
                lambda: delete_booking(
                    self.selected_booking
                ),
                "Бронирование удалено"
            )

    # =====================================
    # ОБНОВЛЕНИЕ ДАННЫХ
    # =====================================

    def refresh(self):
        try:
            users = get_all_users()
            tables = get_all_tables()
            bookings = get_all_bookings()

            self.user_tree.delete(
                *self.user_tree.get_children()
            )

            self.table_tree.delete(
                *self.table_tree.get_children()
            )

            self.booking_tree.delete(
                *self.booking_tree.get_children()
            )

            for user in users:
                self.user_tree.insert(
                    "", "end",
                    values=(
                        user["id"],
                        user["name"],
                        user["phone"]
                    )
                )

            for table in tables:
                self.table_tree.insert(
                    "", "end",
                    values=(
                        table["id"],
                        table["table_number"],
                        table["seats"]
                    )
                )

            self.user_options = {
                f'{u["id"]} — {u["name"]}': u["id"]
                for u in users
            }

            self.table_options = {
                f'№{t["table_number"]} — {t["seats"]} мест':
                t["id"]
                for t in tables
            }

            self.booking_user["values"] = list(
                self.user_options.keys()
            )

            self.booking_table["values"] = list(
                self.table_options.keys()
            )

            self.booking_data = {
                b["id"]: b for b in bookings
            }

            for booking in bookings:
                self.booking_tree.insert(
                    "", "end",
                    values=(
                        booking["id"],
                        booking["user_name"],
                        booking["table_number"],
                        booking["start_time"].strftime(
                            DATE_FORMAT
                        ),
                        booking["end_time"].strftime(
                            DATE_FORMAT
                        )
                    )
                )

            self._clear_user()
            self._clear_table()
            self._clear_booking()

        except Exception as error:
            messagebox.showerror(
                "Ошибка подключения или загрузки",
                str(error)
            )


# =====================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# =====================================

if __name__ == "__main__":
    app = RestaurantApp()
    app.mainloop()
