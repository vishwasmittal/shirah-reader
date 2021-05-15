import curses
import enum
import time
import syllables

from .utils import input_prompt


wpm = 300


class RSVP_SCREEN_OPS(enum.Enum):
    QUIT = 0
    CHANGE_READING_POS = 1
    CHANGE_READING_SPEED = 2
    TOGGLE_NO_DISTRACT_MODE = 3


class RSVPUtils:
    @staticmethod
    def get_wait_time_for_word(word, wps):
        return (1 / wps) * (1 + syllables.estimate(word) ** 2 / 100)

    def process_rsvp_input(user_input, content, line_idx, word_idx, wpm):
        """
        - h: go back 5 words
        - H: go back 20 words
        - l: go forward 5 words
        - L: go forward 20 words
        - q: quit
        - s: decrease wpm by 10 words (min speed: 1)
        - d: increase wpm by 10 words
        """

        def go_back_n_words(n, content, line_idx, word_idx):
            word_idx = word_idx - n
            if word_idx >= 0:
                return line_idx, word_idx
            else:
                line_idx = line_idx - 1
                if line_idx < 0:
                    line_idx, word_idx = 0, 0
                    return line_idx, word_idx
                else:
                    n = -word_idx
                    word_idx = len(content[line_idx].split())
                    return go_back_n_words(n, content, line_idx, word_idx)

        def go_forward_n_words(n, content, line_idx, word_idx):
            word_idx += n
            curr_line_len = len(content[line_idx].split())
            if word_idx < curr_line_len:
                return line_idx, word_idx
            elif line_idx == len(content) - 1:
                return line_idx, curr_line_len - 1
            else:
                # NOTE: line_idx can't be >= len(content)
                n = word_idx - curr_line_len
                line_idx += 1
                word_idx = 0
                return go_forward_n_words(n, content, line_idx, word_idx)

        if user_input == "q":
            operation = RSVP_SCREEN_OPS.QUIT
        elif user_input == "t":
            operation = RSVP_SCREEN_OPS.TOGGLE_NO_DISTRACT_MODE
        elif user_input == "h":
            # go back 5 words
            operation = RSVP_SCREEN_OPS.CHANGE_READING_POS
            line_idx, word_idx = go_back_n_words(5, content, line_idx, word_idx)
        elif user_input == "H":
            # go back 20 words
            operation = RSVP_SCREEN_OPS.CHANGE_READING_POS
            line_idx, word_idx = go_back_n_words(20, content, line_idx, word_idx)
        elif user_input == "l":
            # go forward 5 words
            operation = RSVP_SCREEN_OPS.CHANGE_READING_POS
            line_idx, word_idx = go_forward_n_words(5, content, line_idx, word_idx)
        elif user_input == "L":
            # go forward 20 words
            operation = RSVP_SCREEN_OPS.CHANGE_READING_POS
            line_idx, word_idx = go_forward_n_words(20, content, line_idx, word_idx)
        elif user_input == "s":
            operation = RSVP_SCREEN_OPS.CHANGE_READING_SPEED
            wpm = max(1, wpm - 10)
        elif user_input == "d":
            operation = RSVP_SCREEN_OPS.CHANGE_READING_SPEED
            if wpm == 1:
                wpm = 10
            else:
                wpm += 10
        else:
            raise ValueError(f"Unknown user input: {user_input}")

        return {
            "operation": operation,
            "wpm": wpm,
            "line_idx": line_idx,
            "word_idx": word_idx,
        }

    @staticmethod
    def render_word(chwin, wpm, word, window_width, window_hight):
        # chwin.clear()
        wps = wpm / 60.0
        word_len = len(word)
        t_wait_sec = RSVPUtils.get_wait_time_for_word(word, wps)
        highlight_letter_index = min(4, round(word_len / 2))
        spaces = abs(4 - highlight_letter_index) * " "
        wi_cn = round(window_width / 2) - 5
        chwin.addstr(
            round(window_hight / 2), wi_cn + len(spaces), word[:highlight_letter_index]
        )
        chwin.addstr(
            round(window_hight / 2),
            wi_cn + len(word[:highlight_letter_index]) + len(spaces),
            word[highlight_letter_index],
            curses.color_pair(197),
        )
        chwin.addstr(
            round(window_hight / 2),
            wi_cn + len(word[:highlight_letter_index]) + 1 + len(spaces),
            word[highlight_letter_index + 1 :],
        )

        if "." in word:
            time.sleep(0.2)
        if (
            "," in word
            or "'" in word
            or '"' in word
            or "`" in word
            or "-" in word
            or "(" in word
            or ")" in word
            or ":" in word
        ):
            time.sleep(0.1)
        time.sleep(t_wait_sec)
        # chwin.refresh()


def rsvp(content, y, SCREEN, COLORSUPPORT):
    global wpm
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    rows, cols = SCREEN.getmaxyx()
    hi, wi = rows - 4, cols - 4
    Y, X = 2, 2
    chwin = curses.newwin(hi, wi, Y, X)
    if COLORSUPPORT:
        chwin.bkgd(SCREEN.getbkgd())

    line_idx = y
    total_lines = len(content)
    word_idx = 0
    no_delay_flag = True
    chwin.nodelay(no_delay_flag)
    no_distract_mode = False
    is_distraction_visible = False
    pause_after_operation = False
    while line_idx < total_lines:
        try:
            line = content[line_idx].split()
            words_in_line = len(line)
            while word_idx < words_in_line:
                try:
                    chwin.clear()
                    if not no_distract_mode:
                        # Print Reading stats
                        is_distraction_visible = True
                        chwin.addstr(
                            0,
                            0,
                            (
                                f"Reading Stats:"
                                f"\tLine: {line_idx:05}/{len(content):05}"
                                f"\tWord: "
                                f"{word_idx:02}/{len(content[line_idx].split()):02}"
                                f"\tWPM: {wpm:04}"
                            ),
                        )
                        # render 3 lines (for reference)
                        if line_idx > 0:
                            # line before word
                            chwin.addstr(hi - 3, 0, content[line_idx - 1])
                        if line_idx < len(content) - 1:
                            # line after word
                            chwin.addstr(hi - 1, 0, content[line_idx + 1])

                        # line containing word
                        prefix, prefix_start_pos = " ".join(line[:word_idx]), 0
                        word, word_start_pos = line[word_idx], (
                            len(prefix) + 1 if len(prefix) else 0
                        )
                        suffix, suffix_start_pos = " ".join(line[word_idx + 1 :]), (
                            word_start_pos + len(word) + 1
                        )

                        chwin.addstr(hi - 2, prefix_start_pos, prefix)
                        chwin.addstr(
                            hi - 2, word_start_pos, word, curses.color_pair(197)
                        )
                        chwin.addstr(hi - 2, suffix_start_pos, suffix)

                    elif is_distraction_visible:
                        # clear RSVP distractions by overwriting on them
                        chwin.addstr(0, 0, " " * wi)
                        chwin.addstr(hi - 3, 0, " " * wi)
                        chwin.addstr(hi - 2, 0, " " * wi)
                        chwin.addstr(hi - 1, 0, " " * (wi - 1))
                        is_distraction_visible = False

                    RSVPUtils.render_word(
                        chwin=chwin,
                        wpm=wpm,
                        word=line[word_idx],
                        window_width=wi,
                        window_hight=hi,
                    )
                    chwin.refresh()
                    if pause_after_operation is True:
                        # pause after operation so that brain can get time
                        # to adjust to the change.
                        time.sleep(0.3)
                        pause_after_operation = False

                    user_input = chwin.getkey()
                    if user_input == " ":
                        no_delay_flag = not no_delay_flag
                        chwin.nodelay(no_delay_flag)
                        continue
                    res: dict = RSVPUtils.process_rsvp_input(
                        user_input=user_input,
                        content=content,
                        line_idx=line_idx,
                        word_idx=word_idx,
                        wpm=wpm,
                    )
                    line_idx, word_idx, wpm = (
                        res["line_idx"],
                        res["word_idx"],
                        res["wpm"],
                    )
                    line = content[line_idx].split()
                    words_in_line = len(line)
                    if res["operation"] == RSVP_SCREEN_OPS.QUIT:
                        return line_idx
                    elif res["operation"] == RSVP_SCREEN_OPS.TOGGLE_NO_DISTRACT_MODE:
                        no_distract_mode = not no_distract_mode
                        continue
                    elif res["operation"] == RSVP_SCREEN_OPS.CHANGE_READING_POS:
                        pause_after_operation = True
                        continue
                except ValueError:
                    continue
                except (curses.error) as e:
                    if str(e) != "no input":
                        raise e

                word_idx += 1

            word_idx = 0
            line_idx += 1
        except KeyboardInterrupt as e:
            if no_delay_flag is True:
                no_delay_flag = False
                chwin.nodelay(no_delay_flag)
            keybinding_msg = "Current wpm: " + str(wpm) + " Enter new wpm: "
            try:
                option = input_prompt(keybinding_msg)
                wpm = int(option)
            except ValueError as e:
                return line_idx
            except KeyboardInterrupt as e:
                return line_idx

            if no_delay_flag is False:
                no_delay_flag = True
                chwin.nodelay(no_delay_flag)

    return line_idx
