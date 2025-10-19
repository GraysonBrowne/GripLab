# ui/modals.py
"""Modal dialog layouts for GripLab application."""

import panel as pn


def create_settings_layout(settings_widgets, save_callback, dir_callback):
    """Create application settings modal layout."""
    # Bind callbacks
    pn.bind(save_callback, settings_widgets.save_button.param.clicks, watch=True)
    pn.bind(dir_callback, settings_widgets.data_dir_btn.param.clicks, watch=True)

    return pn.Column(
        pn.pane.HTML(
            """<h1>Settings</h1>""",
            styles={
                "height": "40px",
                "line-height": "0px",
                "margin-top": "0px",
                "margin-bottom": "0px",
            },
        ),
        pn.Row(
            settings_widgets.theme_select,
            settings_widgets.colorway_select,
            pn.Column(
                pn.widgets.StaticText(value="Demo Mode"), settings_widgets.demo_switch
            ),
        ),
        pn.Row(settings_widgets.unit_select, settings_widgets.sign_select),
        pn.Row(settings_widgets.data_dir_btn, settings_widgets.data_dir_input),
        pn.Row(pn.layout.HSpacer(), settings_widgets.save_button),
        width=800,
        margin=(0, 20),
    )


def create_plot_settings_layout(plot_settings_widgets):
    """Create plot settings modal layout."""
    return pn.Column(
        pn.pane.HTML(
            """<h1>Plot Settings</h1>""",
            styles={
                "height": "40px",
                "line-height": "0px",
                "margin-top": "0px",
                "margin-bottom": "0px",
            },
        ),
        plot_settings_widgets.title,
        plot_settings_widgets.subtitle,
        plot_settings_widgets.x_label,
        plot_settings_widgets.y_label,
        plot_settings_widgets.z_label,
        plot_settings_widgets.c_label,
        plot_settings_widgets.color_map,
        plot_settings_widgets.font_size,
        plot_settings_widgets.marker_size,
        width=450,
        margin=(0, 20),
    )


def create_removal_dialog(dataset_name, confirm_callback, cancel_callback):
    """Create dataset removal confirmation dialog."""
    confirm_btn = pn.widgets.Button(
        name="Remove Dataset", button_type="primary", margin=(10, 10, 0, 10), width=200
    )

    cancel_btn = pn.widgets.Button(
        name="Cancel", button_type="default", margin=(10, 10, 0, 10), width=200
    )

    # Bind callbacks
    pn.bind(confirm_callback, confirm_btn.param.clicks, watch=True)
    pn.bind(cancel_callback, cancel_btn.param.clicks, watch=True)

    confirm_html = f"""<p>Are you sure that you want to remove
        <b>{dataset_name}</b> from the session?</p>"""

    return pn.Column(
        pn.pane.HTML(
            """<h1>Remove Dataset?</h1>""",
            styles={
                "height": "40px",
                "line-height": "0px",
                "margin-top": "0px",
                "margin-bottom": "0px",
            },
        ),
        pn.pane.HTML(confirm_html, styles={"font-size": "16px"}, margin=(0, 15, 0, 15)),
        pn.Row(pn.layout.HSpacer(), confirm_btn, cancel_btn),
        width=440,
        margin=(0, 20),
    )
