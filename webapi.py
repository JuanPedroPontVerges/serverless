import json
import requests
from requests.structures import CaseInsensitiveDict
from apps.Parser.Container import Container, Pos
from typing import BinaryIO
from collections import defaultdict, Counter
import requests
import pdftotext
import re
import typing as t
import unicodedata


def handler(event, context):
    data = json.loads(event['body'])
    clearing_id = data["clearing_id"]
    access_token = data["access_token"]
    date = data["requestData"]["date"]
    establishmentID = data["requestData"]["establishment_id"]
    url = "https://comercios.prismamediosdepago.com/api/bff-liquidation/private/pdf?type=daily&date=" + \
        date + "&establishmentId=" + establishmentID
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = "Bearer " + access_token
    response = requests.get(url, headers=headers)
    with open('/tmp/' + establishmentID + date + '.pdf', 'wb') as fd:
        fd.write(response.content)
    file = open('/tmp/' + establishmentID + date + '.pdf', 'rb')
    return {"statusCode": 200, "body": json.dumps({"data": obtain_discounts(file, clearing_id)})}


def obtain_discounts(file_, clearing_id):
    total, response_data = group_discounts(file_)
    print({
        'clearing': clearing_id,
        'response_data': response_data,
        **total
    })
    return {
        'clearing': clearing_id,
        'response_data': response_data,
        **total
    }


def group_discounts(file_):

    total = defaultdict(float)
    discount_data = parse_discounts(file_)
    general = group_sections(discount_data)

    # arancel
    total["arancel"] = sum(
        (sum(v.values()) for _, v in general.get("Arancel").items())
    )

    # impuestos
    for k, v in general.get("Deduc Impositivas").get("Impuestos").items():
        if "IVA 21" in k:
            total["tax_iva21"] += v
        elif "IVA 10" in k:
            total["tax_iva10"] += v
        else:
            total["tax_othres"] += v

    # percepciones
    for k, v in general.get("Deduc Impositivas").get("Percepciones").items():
        if "IB" in k:
            total["perception_iibb"] += v
        elif "IVA" in k:
            total["perception_iva"] += v
        else:
            total["perception_other"] += v

    # retenciones
    for k, v in general.get("Deduc Impositivas").get("Retenciones").items():
        if "IB" in k:
            total["retention_iibb"] += v
        elif "IVA" in k:
            total["retention_iva"] += v
        elif "Ganancias" in k:
            total["retention_ganancias"] += v
        else:
            total["retention_others"] += v

    # promotions
    total["promotion"] = sum(
        (sum(v.values())
         for _, v in general.get("Dto por Ventas de Campana").items())
    )

    # installment
    total["installment"] = sum(
        (sum(v.values())
         for _, v in general.get("Serv Costos Financieros").items())
    )

    # qs = Discount.objects.filter(clearing__id=settlement.id)  # ESTO ES NODE
    # all_discounts = get_all_discounts(qs)
    # total["others"] = sum(all_discounts.values()) - \
    #     sum(total.values()) if all_discounts.values() else 0.0

    return total, discount_data


def parse_discounts(file_: BinaryIO = None, path: str = None) -> dict:
    """parse a given pdf file return all discounts in a json like object

    Discounts in prisma pdfs are separated in sections and sub sections

    øsection:

        - sub section 1:

            discounts

        - sub section 2:

            discounts

    this parser create a json like objects with discounts discriminated with this section
    and subsection logic.

    IMPOORTANT:

        'ø' represent a section
        '-' represent a sub section, with some edge cases, that instead represent a discount

    :param  file_   : pdf file to parse, defaults to None
    :type   file_   : BinaryIO, optional

    :param  path    : path to pdf file to parse, defaults to None
    :type   path    : str, optional

    :return         : parsed discounts
    :rtype          : dict
    """

    # this sections are edge cases where '-' doenst represent a sub section
    SECTIONS_SLICE_BLACK_LIST = [
        "Serv Tarjeta No Presente", "Arancel"]  # "Serv Ecommerce"

    # pdf object
    pdf = None

    # data where store parsed discounts in sections and subsections
    data = dict()

    # try to create a pdftotext object
    try:

        if path:
            # open pdf from path
            with open(path, "rb") as f:
                # create a pdftotext object
                pdf = pdftotext.PDF(f)

        # if no path is given user the file object
        else:
            pdf = pdftotext.PDF(file_)

    # if error ocurrin while creatin the pdf object return empty dict
    except Exception as e:
        print(f"Prisma Error parsing discounts {e}")
        return data

    # create container
    container = Container(pdf[0].split("\n"))

    # ------------------------------------- #
    # Get table slice where discount appear #
    # ------------------------------------- #

    if container.string_in_container("Total del día"):
        # get table slice
        container = container.slice("PERIODO LIQUIDADO", "Total del día")
    # get table slice
    else:
        container = container.slice("PERIODO LIQUIDADO", "IMPORTANTE")

    # get discounts title position
    pos = container.find("DETALLE DE DESCUENTOS")

    # if no discount title, this page can not be parsed, so continue with the next one
    if pos.row == None and pos.col == None:
        return data

    # isolate discounts from table - get discounts block slice
    block_slice = container.slice(
        start=Pos(pos.row + 2, pos.col - 15), stop=Pos(None, None))

    # strip rows - remove blank space arrond the rows
    block_slice = Container([row.strip() for row in block_slice if row])

    # get discounts sections
    for section in block_slice.slice_in("ø", start_with=True):

        # parse section title
        s_key = parse_string(section[0])
        # remove duplicated blank space
        s_key = re.sub(r" +", " ", s_key)

        # remove '(*)' from section title
        s_key = s_key.replace("(*)", "").strip()

        # remove section title from container
        del section.data[0]

        # where sub sections will be store
        sub_section_content = defaultdict(list)

        # split in sub sections
        sub_sections = section.slice_in("-", start_with=True)

        # iterate through sub sections
        for sub_section in sub_sections:

            # parse sub section title
            sub_key = parse_string(sub_section[0]).replace("-", "")

            # if there are subsections and section is not and edge case
            # where '-' instead represent a discount
            if len(sub_section.data) > 1 and not contains(s_key, SECTIONS_SLICE_BLACK_LIST):
                # remove sub title section
                del sub_section.data[0]

            # if there is not sub section, sub section title will be equal of section title
            else:
                sub_key = s_key

            # normalize a specific title, to avoid create two diferen sub sections
            # when actually are the same, with a typo
            if "BonifCargo" in sub_key:
                sub_key = "Bonif Cargo por"

            # parsed subsection data where one discount is not in separate in two lines
            parsed_sub_section = list()

            # discount index
            index = 0

            # fix two lines discounts
            while index < len(sub_section.data):
                # logic is simple, if one line does not has a '$' and the next one does,
                # it's a discount separated in two lines

                try:

                    # check if discount is splited in two lines
                    if not "$" in sub_section[index] and "$" in sub_section[index + 1]:
                        # merge two discounts
                        parsed_sub_section.append(
                            sub_section[index] + " " + sub_section[index + 1])
                        # skip the merged discounts
                        index += 2
                        # continue to next discount
                        continue

                except IndexError:
                    break

                # if at this point '$' is not present in discount, it's because
                # it's not a discount
                if "$" in sub_section[index]:
                    # append discount to parsed sub section list
                    parsed_sub_section.append(sub_section[index])

                # move to net discount
                index += 1

            # iterate through parsed subsections
            for row in parsed_sub_section:

                # get discount name and amount
                k, v = row.split("$")

                # parse discount name
                key = parse_string(k).replace("-", "")
                # parse discount amount
                value = parse_string(v)

                # remove duplicated blank space in discount name
                key = re.sub(r" +", " ", key)

                # if amount it's not float (decimal number)
                # skip this discount
                if not isinstance(value, float):
                    continue

                # remove a typo from a discount name
                if "Bonif Cargo" in sub_key:
                    # remove 'por' in 'por Servicio 03/20'
                    if re.search(r"por Servicio \d+[/]\d+", key):
                        key = re.sub(r"por (Servicio \d+[/]\d+)", r"\1", key)

                # store discount in sub section
                sub_section_content[sub_key].append({key: value})

        # sotre sub_section_content
        data[s_key] = dict(sub_section_content)

    # return discount data with section and subsection parsed
    return data


def group_sections(discount_data: t.Dict[str, t.Any]) -> dict:
    # get sub sections grouped
    group = group_sub_sections(discount_data)
    # organize discount sections and subsections by discount type
    GROUPS = {
        "Arancel": ["Arancel", "Bonif Cargo por", "Serv Ecommerce", "Serv Tarjeta No Presente", "Operaciones Internacionales"],
        "Deduc Impositivas": ["Impuestos", "Percepciones", "Retenciones"],
        "Dto por Ventas de Campana": ["Ventas Tj Debito c/dto"],
        "Serv Costos Financieros": ["Plan Cuotas"],
        "Servicio LaPos": ["Servicio LaPos"],
    }
    # subsection grouped object
    data = {
        # create section key -> ej: Deduc Impositivas
        key: {
            # get subsection objects -> ej: Deduc Impositivas {"Impuestos": ..., "Percepciones": ..., "Retenciones": ...}
            v: group.get(v) for v in values
            # iterate through GROUPS items
        } for key, values in GROUPS.items()
    }
    # final object to return
    results = dict()
    # iterate through sections
    for fk, fv in data.items():
        # create a fresh new sub sections
        sub_section = defaultdict(Counter)
        # iterate through sub sections
        for sk, sv in fv.items():
            # add all equals discounts and store them in a new fresh sub section
            sub_section[sk].update(sv)
        # store a new fresh sub section in the final object
        results[fk] = sub_section
    # return all sub sections grouped and added
    return results


def group_sub_sections(discount_data: t.Dict[str, t.Any]) -> dict:

    # grouped sub sections
    general = defaultdict(list)

    # iterate trhough all sections
    for kf, vf in discount_data.items():
        # iterate trhough all subsections
        for ks, vs in vf.items():
            # add discounts to sub section
            general[ks].extend(vs)

    # final resul to return
    results = dict()

    # iterate through sub sections
    for key in general:

        # added discounts
        disc = Counter()

        # iterate through sub sections discounts
        for elm in general.get(key):
            # add sub sections discounts to disc
            disc.update(Counter(elm))

        # set added discounts to final result
        results[key] = dict(disc)

    # returl final result
    return results


def parse_string(string):

    string = remove_accents(
        string.strip().replace('.', '').replace(',', '.')
    ).encode("ascii", "ignore").decode("utf-8")

    try:
        string = float(string)
    except:
        pass

    return string


def contains(elm, black_list):

    for bl in black_list:
        if bl.lower() in elm.lower():
            return True

    return False


def remove_accents(string: str) -> str:
    return u''.join(
        [
            c for c in unicodedata.normalize('NFKD', string)
            if not unicodedata.combining(c)
        ]
    )
