# python built in modules
from collections import namedtuple
from itertools import takewhile

# third party imports

# own modules import
from apps.Parser.utils import Options

# type hint imports
from typing import List, Dict, Optional

# -----------------------------------------------------------------------------------------------------------------------------

Pos = namedtuple('Pos', 'row col')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Container:

    # -----------------------------------------------------------------------------------------------------------------------------

    def __init__(self, data, *args, **kwargs) -> None:

        # fields
        self.data = list(data)

        # Default values
        self.default_erase_character = '*'

    # -----------------------------------------------------------------------------------------------------------------------------

    def __str__(self) -> str:
        return '\n'.join(self.data)

    # -----------------------------------------------------------------------------------------------------------------------------

    def __iter__(self):
        for row in self.data:
            yield row

    # -----------------------------------------------------------------------------------------------------------------------------

    def __getitem__(self, row):
        return self.data[row]

    # -----------------------------------------------------------------------------------------------------------------------------

    def __delitem__(self, row: int):
        del self.data[row]

    # -----------------------------------------------------------------------------------------------------------------------------

    @property
    def copy(self) -> 'Container':
        return Container(self.data)

    # -----------------------------------------------------------------------------------------------------------------------------

    def save(self, filename: str) -> None:
        ''' Save data to given filename '''

        with open(filename, 'w') as f:
            for row in self.data:
                f.write(f'{row}\n')

    # -----------------------------------------------------------------------------------------------------------------------------

    def reversed(self, options):

        for index in reversed(range(len(self.data))):

            if options.get('only_index') is True:
                yield index

            elif options.get('include_index') is True:
                yield (index, self.data[index])

            else:
                yield self.data[index]

    # -----------------------------------------------------------------------------------------------------------------------------

    def filter(self, predicate, erase=False):

        for index, row in self.reversed(Options(include_index=True)):

            if predicate(row) is True:

                if erase is True:
                    del self.data[index]

                yield row

    # -----------------------------------------------------------------------------------------------------------------------------

    def string_in_container(self, strings) -> bool:

        if isinstance(strings, str):
            strings = list(strings)

        if not isinstance(strings, list):
            raise ValueError(f'{strings} must be List[str]')

        for row in self.data:
            for string in strings:
                if string in row:
                    return True

        return False

    # -----------------------------------------------------------------------------------------------------------------------------

    def find(self, string=None, start=0, stop=None, start_with=False) -> Pos:
        ''' Find given string in container '''

        if isinstance(string, int):
            return Pos(row=string, col=0)
        if not isinstance(string, str):
            raise ValueError()

        for index, row in enumerate(self.data[start:stop]):
            col = row.find(string)
            if col != -1:
                # chec if string is at the start of row
                if start_with:
                    if col != 0:
                        continue
                return Pos(row=start + index, col=col)

        return Pos(None, None)

    # -----------------------------------------------------------------------------------------------------------------------------

    def _block_slice(self, start=None, stop=None, step=None, options=None):
        ''' Get a block from container '''

        sRow = slice(start.row, stop.row, step)
        sCol = slice(start.col, stop.col, step)

        # set step to 1 by default
        if step is None:
            step = 1

        # Get slice from container
        slice_ = [

            row[sCol] for row in self.data[sRow]
        ]

        char = options.get('char', self.default_erase_character)

        if options.get('erase') is True:
            # 'erase' data from container
            for row, rep in zip(range(start.row, stop.row, step), slice_):
                self.data[row] = self.data[row].replace(rep, char * len(rep))

        return Container(slice_)

    # -----------------------------------------------------------------------------------------------------------------------------

    def _row_slice(self, start=None, stop=None, step=None, erase=False):
        ''' Get rows from container '''

        if isinstance(stop, tuple):
            stop = stop.row
        if isinstance(start, tuple):
            start = start.row

        sObject = slice(start, stop, step)

        container = Container(self.data[sObject])

        # erase slice
        if erase:
            del self.data[sObject]

        # return slice
        return container

    # -----------------------------------------------------------------------------------------------------------------------------

    def slice(self, start=None, stop=None, step=None, options=None):

        if isinstance(start, str):
            start = self.find(start).row
        if isinstance(stop, str):
            stop = self.find(stop).row

        if options is None:
            options = dict()
        if start is None:
            start = Pos(None, None)
        if stop is None:
            stop = Pos(None, None)

        if isinstance(start, tuple) and isinstance(stop, tuple):
            return self._block_slice(start, stop, step, options)

        return self._row_slice(start, stop, step, options.get('erase', False))

    # -----------------------------------------------------------------------------------------------------------------------------

    def slice_in(self, string: str, start_with=False, options=None):

        if not isinstance(string, str):
            raise ValueError(f'string: {string} is not a str value')

        options = options if not options is None else dict()
        char = options.get('char', self.default_erase_character)

        container = self

        if not options.get('erase') is True:
            container = Container(self.data)

        slices = []

        while container.string_in_container(string):

            start = container.find(string, start_with=start_with).row
            if start is None:
                start = 0
            stop = container.find(string, start=start + 1,
                                  start_with=start_with).row

            slices.append(container.slice(

                start=start,
                stop=stop,
                options=Options(erase=True)
            ))

        return slices

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


if __name__ == "__main__":

    import pdftotext

    # Load your PDF
    with open('clearings/clearing_22-11-2019.pdf', 'rb') as f:
        pdf = pdftotext.PDF(f)

    container = Container(pdf[0].split('\n'))
    container.save('atemp/text.txt')

    # container.slice(0, -3, options=Options(erase=True))

    container = container.slice(
        start='FECHA DE PAGO', stop='Total del día', options=Options(erase=True))
    container.save('atemp/slice.txt')

    # c = container.slice(

    #     start       = Pos(row=60, col=0),
    #     stop        = Pos(row=72, col=22),
    #     options     = Options(erase=True, char='+')
    # )

    c = container.slice_in('Fecha de presentación')
    c.save('atemp/slice_in.txt')

    container.save('atemp/final.txt')
