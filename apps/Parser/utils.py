# python built in modules
from datetime import datetime
import multiprocessing as mp
import multiprocessing.pool
import multiprocessing
import json
import time
import re

# type hint
from typing import Sequence

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class NoDaemonProcess(multiprocessing.Process):
    @property # type: ignore
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class NoDaemonContext(type(multiprocessing.get_context())): # type: ignore
    Process = NoDaemonProcess

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class NoDeamonPool(multiprocessing.pool.Pool):
    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super().__init__(*args, **kwargs)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# -----------------------------------------------------------------------------------------------------------------------------

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Time:

    # -----------------------------------------------------------------------------------------------------------------------------

    def __init__(self, time_):
        self._time = time_

    # -----------------------------------------------------------------------------------------------------------------------------

    def __str__(self) -> str:
        return f'{self._time}'

    # -----------------------------------------------------------------------------------------------------------------------------

    @property
    def time (self): return self._time

    # -----------------------------------------------------------------------------------------------------------------------------

    @property
    def formated (self):
        return f'{self._time // 60.:.2f} m - {self._time % 60:.2f} s' if self._time >= 60 else f'0 m - {self.time:.2f} s'

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def timeit(method):

    def timed(*args, **kw):

        # start timing
        ts = time.time()
        
        # call method
        result = method(*args, **kw)

        # calculate time delta
        te = time.time() - ts

        # log delta time
        # log(f'"{method.__name__.upper()}" - scraper_time: {te:.2f} s ', line_brake=False)

        return result, Time(te)

    return timed

# -----------------------------------------------------------------------------------------------------------------------------

def log (log=None, filename=None, base_root=None, line_brake=True):

    if base_root    is None: base_root = 'atemp'
    if log          is None: log = ''
    if filename     is None: filename = 'logs'

    if line_brake: log += '\n'
    if base_root[-1] == '/': base_root == base_root[:-1]

    with open(f'{base_root}/{filename}.log', 'a') as f:
        f.write(log)

# -----------------------------------------------------------------------------------------------------------------------------

def log_file (resp, filename, base_root=None):

    if base_root is None:
        base_root = 'atemp'

    try:
        with open(f'{base_root}/{filename}.pdf', 'wb') as f:
            f.write(resp.content)
    except Exception as e: print (f'LOG_FILE ERROR: {e}')

# -----------------------------------------------------------------------------------------------------------------------------

def log_response (resp, filename, base_root=None):

    if base_root is None:
        base_root = 'atemp'

    try:
        with open(f'{base_root}/response/{filename}.html', 'w') as f:
            f.write(resp.text)
    except Exception as e: print (f'LOG_RESPONSE ERROR: {e}')

# -----------------------------------------------------------------------------------------------------------------------------

def find_reg_in_list(reg, iterable):                                                    

    for it in iterable:
        if re.search(reg, it): return True

# -----------------------------------------------------------------------------------------------------------------------------

def log_json (data, filename, base_root=None):

    if base_root is None:
        base_root = 'atemp'

    try:
        with open(f'{base_root}/json/{filename}.json', 'a') as f:
            f.write(f'{data},')
    except Exception as e: print (f'LOG_JSON ERROR: {e}')

# -----------------------------------------------------------------------------------------------------------------------------

def group(iterable, n):
    """group([0,3,4,10,2,3], 2) => [(0,3), (4,10), (2,3)]
    
    Group a list into consecutive n-tuples. Incomplete tuples are
    discarded e.g.
    
    >>> group(range(10), 3)
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
    """

    iterable = list(iterable)

    if len(iterable) == 0: return (iterable, )

    while len(iterable) % n != 0:
        iterable.append(iterable[-1] + 1)

    g_pages = list(
        zip(
            *[ iterable[i::n] for i in range(n) ]
        )
    )

    l_elm = g_pages[-1][-1]

    return g_pages + [tuple(
        range(
            l_elm + 1, l_elm + (iterable[-1] - l_elm)
        )
    )]

# -----------------------------------------------------------------------------------------------------------------------------

def Options(*args, **kwargs):
    return { **kwargs }

# -----------------------------------------------------------------------------------------------------------------------------

def complete_date(date=None, format_=None):

    if date is None: return

    if format_ is None: format_ = '%Y-%m-%d'

    return str(datetime.strptime(date, format_))

# -----------------------------------------------------------------------------------------------------------------------------

def parse_date (encoded_date, format_=None):

    if format_ is None: format_ = '%Y-%m-%d %H:%M:%S'

    return datetime.fromtimestamp(encoded_date / 1000)  \
        .strftime(format_) if not encoded_date is None else None

# -----------------------------------------------------------------------------------------------------------------------------

def remove_accents(string : str) -> str:
    return u''.join(
        [
            c for c in unicodedata.normalize('NFKD', string)
            if not unicodedata.combining(c)
        ]
    )

# -----------------------------------------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------------------------------------------

def contains_all(elm, white_list):

    for bl in white_list:
        if not bl.lower() in elm.lower(): return False

    return True

# -----------------------------------------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------------------------------------------

def json_from_container (container, slice_by : str, k_parser=None, v_parser=None):
    ''' return json from a container slicing by given string '''

    remaining = container.copy

    if k_parser is None: k_parser = lambda k: k
    if v_parser is None: v_parser = lambda v: v

    # return json and container with lines that cant be parsed
    return (

        json.dumps({
            
            
                remove_accents(
                
                    k_parser(k)

                ) : v_parser(v)

            for k, v, *_ in (

                line.split(slice_by)

                    for line in remaining.filter (
                        lambda row: slice_by in row,
                        erase = True
                    )
                )

        }), remaining, # coma avoid return generator
    )

# -----------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    
    from apps.Parser.Container import Container

    container = Container ([
        'Resumen Diario de Liquidaciones',
        'HOJA',
        'FECHA DE EMISION:         21/11/2019',
        'Nº DE RESUMEN:            000000030975',
        'PAGADOR:                  191 BANCO CREDICOOP',
        'SUCURSAL:                 089 MAR DEL PLATA CENTRO',
        'DOMICILIO:                INDEPENDENCIA 1844 CP 7600',
        'Nº DE CUIT:               30-57142135-2',
        'RESP./CARACTER:           Resp.Inscripto',
        'Nº AG.RET.ING.BRUTOS:     00086000409000',
    ])
