# Align View

Align View is a simple desktop utility that allows you to overlay a semi-transparent, movable, and resizable image on top of your screen. It's perfect for artists, designers, and developers who need to trace, align, or compare designs with pixel-perfect precision.

<img width="672" height="312" alt="Image" src="https://github.com/user-attachments/assets/2c259d1c-b159-4b47-8fef-565d378287fd" /> 

* **Adjustable Overlay:** Control the opacity, scale, and rotation.
* **Easy Controls:** Use the mouse wheel, keyboard shortcuts, or the control panel for quick adjustments.
* **Precision Alignment:** Nudge the overlay pixel by pixel with keyboard arrow keys.
* **Drag & Drop:** Open images instantly by dropping them onto the app.
* **Lock View:** Secure your overlay to prevent accidental changes.

## Controls

### Mouse Controls (on Overlay Window)

* **Move:** Left-click and drag.
* **Zoom:** Mouse Wheel scroll.
* **Rotate:** `Shift` + Mouse Wheel scroll.
* **Opacity:** `Ctrl` + Mouse Wheel scroll.
* **Help:** Right-click to show shortcuts.

### Keyboard Controls (on Overlay Window)

* **Move 1px:** `Ctrl` + Arrow Keys.
* **Move 10px:** `Shift` + Arrow Keys.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/suratlayek/Align-View.git
    cd Align-View
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the application, simply execute the `align_view.py` script:

```bash
python align_view.py
```
## How to Use the UI File
The UI is managed in `src/resources/align_view_ui.ui`. If you make changes to this file using Qt Designer, you will need to regenerate the Python UI file (`align_view_ui.py`) using the following command:

```bash
pyuic5 -x src/resources/align_view_ui.ui -o src/align_view_ui.py
```
Similarly, if you update your resources (icons, QSS), you must recompile the `resources.qrc` file:
```bash
pyrcc5 src/resources/resources.qrc -o src/resources_rc.py
```
## Acknowledgements

This project uses the **Adaptic** theme, a beautiful QSS stylesheet created by **DevSec Studio**. Thanks to DevSec Studio for making their work available to the community.

* You can find the original theme here: [[Link to the website for adaptic.qss](https://qss-stock.devsecstudio.com/templates.php)]
