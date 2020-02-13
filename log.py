from progress.bar import IncrementalBar

def to_color(s, c):
    return f'\x1b[{c}m{s}\x1b[0m' if use_color else s

def out_line(s='', color=37, indent=0, thread_name=None):
    t = ''
    if thread_name is not None and show_threads:
        t = to_color(f'<{thread_name}> ', thread_color)
    print(t + ' ' * indent + to_color(s, color))

def out(s='', color=37, indent=0, thread_name=None):
    for line in s.split('\n'):
        out_line(line, color, indent, thread_name)

def get_progress_bar(**kwargs):
    bar = IncrementalBar(**kwargs)
    bar.suffix = "%(index)d / %(max)d (%(elapsed_td)s)"

    return bar


use_color = True
show_threads = True
thread_color = 34


# stuff for progress bars
export_task_count = 0
filtered_export_task_count = 0
