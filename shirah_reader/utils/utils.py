import curses


def input_prompt(prompt, SCREEN, COLORSUPPORT):
    # prevent pad hole when prompting for input while
    # other window is active
    # pad.refresh(y, 0, 0, x, rows-2, x+width)
    rows, cols = SCREEN.getmaxyx()
    stat = curses.newwin(1, cols, rows - 1, 0)
    if COLORSUPPORT:
        stat.bkgd(SCREEN.getbkgd())
    stat.keypad(True)
    curses.echo(1)
    curses.curs_set(1)

    init_text = ""

    stat.addstr(0, 0, prompt, curses.A_REVERSE)
    stat.addstr(0, len(prompt), init_text)
    stat.refresh()

    try:
        while True:
            ipt = stat.getch()
            if ipt == 27:
                stat.clear()
                stat.refresh()
                curses.echo(0)
                curses.curs_set(0)
                return
            elif ipt == 10:
                stat.clear()
                stat.refresh()
                curses.echo(0)
                curses.curs_set(0)
                return init_text
            elif ipt in {8, curses.KEY_BACKSPACE}:
                init_text = init_text[:-1]
            elif ipt == curses.KEY_RESIZE:
                stat.clear()
                stat.refresh()
                curses.echo(0)
                curses.curs_set(0)
                return curses.KEY_RESIZE
            # elif len(init_text) <= maxlen:
            else:
                init_text += chr(ipt)

            stat.clear()
            stat.addstr(0, 0, prompt, curses.A_REVERSE)
            stat.addstr(
                0,
                len(prompt),
                init_text
                if len(prompt + init_text) < cols
                else "..." + init_text[len(prompt) - cols + 4 :],
            )
            stat.refresh()
    except KeyboardInterrupt:
        stat.clear()
        stat.refresh()
        curses.echo(0)
        curses.curs_set(0)
        return
