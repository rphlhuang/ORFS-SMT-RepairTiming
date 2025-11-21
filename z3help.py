from z3 import is_true

def extract_buffers(model, buffer_sizes, prefix="S_"):
    choices = {}

    for d in model.decls():
        name = d.name()

        if not name.startswith(prefix):
            continue

        val = model[d]
        if not is_true(val):
            continue

        # remove the "S_"
        rest = name[len(prefix):]

        # Find which cell this corresponds to by matching suffix
        selected_cell = None
        slot_name = None

        for cell in buffer_sizes:
            suffix = "_" + cell
            if rest.endswith(suffix):
                selected_cell = cell
                slot_name = rest[: -len(suffix)]
                break

        if selected_cell is None:
            continue

        # Now we have e.g. slot_name="buf_slot_1", selected_cell="BUF_X16"
        choices[slot_name] = selected_cell

    return choices