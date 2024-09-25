import flet as ft
import datetime
import threading
from automation.search import initialize

log_text = ft.Text("")  # global log element

# Function to update the log screen
def update_log(page, message):

    current_log = log_text.value.splitlines()
    current_log.append(message)
    
    # Keep the last 10 log messages

    if len(current_log) > 10:
        current_log = current_log[-10:]
    
    # Update the log_text with the last 10 lines
    log_text.value = "\n".join(current_log)
    log_text.update()  # refresh the log text on the screen

def main_page(page: ft.Page):
    
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.clean()

    # Variables to store button references
    since_button = ft.ElevatedButton()
    until_button = ft.ElevatedButton()
    since_date = None  # To store the selected 'since' date
    until_date = None  # To store the selected 'until' date

    # Function to handle date selection change
    def handle_change(e, button_type):
        nonlocal since_date, until_date
        selected_date = e.control.value
        if button_type == 'since':
            since_button.text = f"since: {selected_date.strftime('%d-%m-%Y')}"
            since_date = selected_date
            page.update()
        elif button_type == 'until':
            until_button.text = f"until: {selected_date.strftime('%d-%m-%Y')}"
            until_date = selected_date
            page.update()

    def handle_dismissal():
        pass

    # Function to pass values to initialize() and switch to log page
    def go_to_log_page(e):
        # Extract input and date values
        user = user_input.value
        password = pass_input.value
        target = target_user.value
        since = since_date.strftime('%d-%m-%Y') if since_date else None
        until = until_date.strftime('%d-%m-%Y') if until_date else None

        # Validate that all fields are filled
        if not user or not password or not target or not since or not until:
            error_message.value = "All fields are required!"
            error_message.color = "red"
            page.update()
            return  # Stop the function if validation fails

        # Clear error message if validation passes
        error_message.value = ""
        
        # Switch to log page
        log_page(page)

        # Run initialize() in a separate thread to avoid blocking the UI
        threading.Thread(target=initialize, args=(user, password, target, since, until, lambda msg: update_log(page, msg))).start()

        page.update()

    # Input fields on the main screen
    user_input = ft.TextField(label="your x's user", width=300, content_padding=20)
    pass_input = ft.TextField(label="your x's pass", width=300, content_padding=20, password=True)
    target_user = ft.TextField(label="get from @", width=300, content_padding=20)

    # Get the current day for calendar config
    today = datetime.datetime.now()
    
    since_button = ft.ElevatedButton(
        'since: ',
        width=300,
        style=ft.ButtonStyle(
            shape=ft.BeveledRectangleBorder(radius=3), 
            padding=20, 
            alignment=ft.alignment.center_left,
            color={
                ft.ControlState.HOVERED: ft.colors.BLACK,
                ft.ControlState.DEFAULT: ft.colors.BLACK,
            }
        ),
        on_click=lambda e: page.open(
            ft.DatePicker(
                first_date=datetime.datetime(year=today.year-1, month=today.month, day=today.day),
                last_date=datetime.datetime(year=today.year, month=today.month, day=today.day),
                on_change=lambda e: handle_change(e, 'since'),
                on_dismiss=lambda e: handle_dismissal(),
            )
        ),
    )
    
    until_button = ft.ElevatedButton(
        'until: ',
        width=300,
        style=ft.ButtonStyle(
            shape=ft.BeveledRectangleBorder(radius=3), 
            padding=20, 
            alignment=ft.alignment.center_left,
            color={
                ft.ControlState.HOVERED: ft.colors.BLACK,
                ft.ControlState.DEFAULT: ft.colors.BLACK,
            }
        ),
        on_click=lambda e: page.open(
            ft.DatePicker(
                first_date=datetime.datetime(year=today.year-1, month=today.month, day=today.day),
                last_date=datetime.datetime(year=today.year, month=today.month, day=today.day),
                on_change=lambda e: handle_change(e, 'until'),
                on_dismiss=lambda e: handle_dismissal(),
            )
        ),
    )
    
    go_button = ft.ElevatedButton(
        'Scrape!', 
        style=ft.ButtonStyle(
            shape=ft.ContinuousRectangleBorder(radius=10), 
            padding=30, 
            alignment=ft.alignment.center,
        ),
        on_click=go_to_log_page  # Switch to the log page when clicked
    )

    error_message = ft.Text(value="", size=14, color="red")

    page.add(
        ft.Container(
            content=ft.Column(
            [
                user_input,
                pass_input,
                target_user,
                since_button,
                until_button,
                ft.Container(height=10),
                go_button,
                ft.Container(height=10),
                error_message, 
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,  
            ),
        )
    )

# Log screen
def log_page(page: ft.Page):

    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.clean()  # clear previous screen content

    display_log = ft.Container(
            content=log_text, 
            height=200,
        )
    
    close_button = ft.ElevatedButton(
            "Close App",
            on_click=lambda e: page.window.close() 
        )
    
    credits = ft.Text("get in touch @ github.com/matzalazar", size=12, color='red')

    page.add(
        ft.Container(
            content=ft.Column(
            [
                display_log,
                ft.Container(height=50),
                close_button,
                ft.Container(height=50),
                credits
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,  
            ),
        )
    )
    
    
    page.update()

# Run the app
def main(page: ft.Page):
    page.title = "X-tract"
    main_page(page)

ft.app(target=main)
