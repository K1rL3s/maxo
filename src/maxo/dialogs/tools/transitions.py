import importlib
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from maxo.dialogs.dialog import Dialog
from maxo.dialogs.setup import collect_dialogs
from maxo.dialogs.widgets.kbd import Back, Cancel, Group, Next, Start, SwitchTo
from maxo.fsm import State
from maxo.routing.interfaces import BaseRouter

if TYPE_CHECKING:
    from diagrams import Node

ICON_PATH = (Path(__file__).parent / "icon.png").as_posix()


def _widget_edges(
    nodes: dict[State, "Node"],
    dialog: Dialog,
    starts: list[tuple[State, State]],
    current_state: State,
    kbd: object,
) -> None:
    diagrams_module = importlib.import_module("diagrams")
    edge_factory = diagrams_module.Edge

    def _safe_connect(
        color: str,
        to_state: State | None,
        *,
        style: str | None = None,
    ) -> None:
        if to_state is None:
            return
        to_node = nodes.get(to_state)
        if to_node is None:
            return
        edge = (
            edge_factory(color=color, style=style)
            if style is not None
            else edge_factory(color=color)
        )
        nodes[current_state] >> edge >> to_node

    states = list(dialog.windows.keys())
    if isinstance(kbd, Start):
        _safe_connect("#338a3e", kbd.state)
    elif isinstance(kbd, SwitchTo):
        _safe_connect("#0086c3", kbd.state)
    elif isinstance(kbd, Next):
        idx = states.index(current_state)
        next_state = states[idx + 1] if idx + 1 < len(states) else None
        _safe_connect("#0086c3", next_state)
    elif isinstance(kbd, Back):
        idx = states.index(current_state)
        prev_state = states[idx - 1] if idx > 0 else None
        _safe_connect("grey", prev_state)
    elif isinstance(kbd, Cancel):
        for from_, to_ in starts:
            if to_.group == current_state.group:
                _safe_connect("grey", from_, style="dashed")


def _walk_keyboard(
    nodes: dict[State, "Node"],
    dialog: Dialog,
    starts: list[tuple[State, State]],
    current_state: State,
    keyboards: Sequence[object],
) -> None:
    for kbd in keyboards:
        if isinstance(kbd, Group):
            _walk_keyboard(nodes, dialog, starts, current_state, kbd.buttons)
        else:
            _widget_edges(nodes, dialog, starts, current_state, kbd)


def _find_starts(
    current_state: State,
    keyboards: Sequence[object],
) -> Iterable[tuple[State, State]]:
    for kbd in keyboards:
        if isinstance(kbd, Group):
            yield from _find_starts(current_state, kbd.buttons)
        elif isinstance(kbd, Start):
            yield current_state, kbd.state


def render_transitions(
    router: BaseRouter,
    title: str = "Maxo Dialog",
    filename: str = "maxo_dialog",
    format: str = "png",
) -> None:
    """
    Render a PNG state-transition diagram for all dialogs in the router.

    Requires: pip install maxo[preview] and system graphviz (brew install graphviz).
    """
    try:
        diagrams_module = importlib.import_module("diagrams")
        diagrams_custom_module = importlib.import_module("diagrams.custom")
    except ImportError as exc:
        raise ImportError(
            "Install maxo[preview] and system graphviz to use render_transitions(). "
            "Run: pip install 'maxo[preview]' && brew install graphviz (macOS) "
            "or apt-get install graphviz (Linux).",
        ) from exc
    window_module = importlib.import_module("maxo.dialogs.window")
    cluster_factory = diagrams_module.Cluster
    diagram_factory = diagrams_module.Diagram
    custom_factory = diagrams_custom_module.Custom
    window_class = window_module.Window

    dialogs = [
        dialog for dialog in collect_dialogs(router) if isinstance(dialog, Dialog)
    ]
    with diagram_factory(title, filename=filename, outformat=format, show=False):
        nodes: dict[State, Node] = {}
        for dialog in dialogs:
            with cluster_factory(dialog.states_group_name()):
                for state in dialog.windows:
                    nodes[state] = custom_factory(
                        label=state.state or "",
                        icon_path=ICON_PATH,
                    )

        starts: list[tuple[State, State]] = []
        for dialog in dialogs:
            for state, window in dialog.windows.items():
                if isinstance(window, window_class):
                    starts.extend(_find_starts(state, [window.keyboard]))

        for dialog in dialogs:
            for state, window in dialog.windows.items():
                if not isinstance(window, window_class):
                    continue
                _walk_keyboard(nodes, dialog, starts, state, [window.keyboard])
                if window.preview_add_transitions:
                    _walk_keyboard(
                        nodes,
                        dialog,
                        starts,
                        state,
                        window.preview_add_transitions,
                    )
