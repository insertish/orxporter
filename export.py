import os
import queue
import time

import check
from exception import FilterException
import exif
from export_thread import ExportThread
from dest_paths import format_path
import log






def export(m, filtered_emoji, input_path, formats, path, src_size,
           num_threads, renderer, max_batch, verbose):
    """
    Runs the entire orxporter process, includes preliminary checking and
    validation of emoji metadata and running the tasks associated with exporting.
    """

    # verify emoji (in a very basic way)
    # --------------------------------------------------------------------------
    log.out('Checking emoji...', 36)
    check_result = check.emoji(m, filtered_emoji, input_path, formats, path, src_size,
               num_threads, renderer, max_batch, verbose)

    exporting_emoji = check_result["exporting_emoji"]
    skipped_emoji_count = check_result["skipped_emoji_count"]

    if skipped_emoji_count > 0:
        log.out(f"- {skipped_emoji_count} emoji have been skipped, leaving {len(exporting_emoji)} emoji to export.", 34)

        if not verbose:
            log.out(f"- use the --verbose flag to see what those emoji are and why they were skipped.", 34)
    log.out('- done!', 32)




    # export emoji
    # --------------------------------------------------------------------------
    # declare some specs of this export.
    log.out("Exporting emoji...", 36)
    log.out(f"- {', '.join(formats)}") # print formats
    log.out(f"- to '{path}'") # print out path

    if num_threads > 1:
        log.out(f"- {num_threads} threads")
    else:
        log.out(f"- {num_threads} thread")

    try:
        # start a Queue object for emoji export
        emoji_queue = queue.Queue()

        # put the [filtered] emoji (plus the index, cuz enumerate()) into the queue.
        for entry in enumerate(exporting_emoji):
            emoji_queue.put(entry)

        # initialise the amount of requested threads
        threads = []
        for i in range(num_threads):
            threads.append(ExportThread(emoji_queue, str(i), len(exporting_emoji),
                                        m, input_path, formats, path, renderer))


        # keeps checking if the export queue is done.
        log.bar.max = len(exporting_emoji)
        while True:
            done = emoji_queue.empty()

            log.bar.goto(log.export_task_count)

            # if the thread has an error, properly terminate it
            # and then raise an error.
            for t in threads:
                if t.err is not None:
                    for u in threads:
                        u.kill()
                        u.join()
                    raise ValueError(f'Thread {t.name} failed: {t.err}')

            if done:
                break

            time.sleep(0.01) # wait a little before seeing if stuff is done again.

        # finish the stuff
        # - join the threads
        # - then finish the terminal stuff
        for t in threads:
            t.join()


        log.bar.goto(log.export_task_count)
        log.bar.finish()


    except (KeyboardInterrupt, SystemExit):
        # make sure all those threads are tidied before exiting the program.
        # also make sure the bar is finished so it doesnt eat the cursor.
        log.bar.finish()
        log.out(f'Stopping threads and tidying up...', 93)
        if threads:
            for t in threads:
                t.kill()
                t.join()

        raise


    log.out('- done!', 32)
    if log.filtered_export_task_count > 0:
        log.out(f"- {log.filtered_export_task_count} emoji have been implicitly or explicitly filtered out of this export task.", 34)

    log.export_task_count = 0
    log.filtered_export_task_count = 0




    # exif license pass
    # (currently only just applies to PNGs)
    # --------------------------------------------------------------------------
    if 'exif' in m.license:
        png_files = []
        for e in exporting_emoji:
            for f in formats:
                # png, pngc or avif
                if f.startswith('png') or f.startswith('avif-'):
                    try:
                        png_files.append(format_path(path, e, f))
                    except FilterException:
                        if verbose:
                            log.out(f"- Filtered emoji: {e['short']}", 34)
                        continue
        if png_files:
            log.out(f'Adding license metadata to png files...', 36)
            exif.add_license(png_files, m.license.get('exif'), max_batch)
