import pandas as pd
from datetime import datetime
import matplotlib
from matplotlib import pyplot as plt
from dateutil.relativedelta import relativedelta
import os
import ssl
import math
ssl._create_default_https_context = ssl._create_unverified_context
script_dir = os.path.dirname(__file__)
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
#%%

plt.rcParams.update({'font.size': 17})


CER = {'Sun': '#FFBE4B',
       'Night Sky': '#054169',
       'Ocean': '#5FBEE6',
       'Forest': '#559B37',
       'Flame': '#FF821E',
       'Aubergine': '#871455',
       'Dim Grey': '#8c8c96',
       'Cool Grey': '#42464B'}

text = {'5YearAvg': {'eng': 'Five year average', 'fra': 'Moyenne sur cinq ans'},
        '5YearRange': {'eng': 'Five year range', 'fra': 'Période de cinq ans'},
        'millionbbl': {'eng': 'Million barrels', 'fra': 'Millions de barils'},
        'westernCanada': {'eng': 'Western Canada', 'fra': 'Ouest canadien'},
        'months': {'eng': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                   'fra': ['Janv.', 'Févr.', 'Mars.', 'Avr.', 'Mai', 'Juin', 'Juill.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.']},
        'prices': {'eng': 'Propane spot prices', 'fra': 'Prix du disponible'},
        'pricesUnits': {'eng': 'US cents per gallon', 'fra': 'Cents US/gallon'},
        'cnStrike': {'eng': 'CN strike start (Nov 19, 2019)', 'fra': 'Début de la grève du CN (19 novembre 2019)'},
        'who': {'eng': 'WHO declares public health emergency (Jan 30, 2020)', 'fra': 'Urgence de santé publique déclarée par l’OMS (30 janvier 2020)'}
        }


mode = "prod"


def english_only(col_names):
    return {x: x.split('/')[0].strip() for x in col_names}


def change_units(df):
    for col in df:
        if col not in ['Region', 'Date']:
            df[col] = (df[col]*6.2898)/1000
    return df


def create_regions(df):
    regions = {}
    for r in list(df['Region'].unique()):
        regions[r] = df[df['Region'] == r].copy()

    return regions


def five_year_average(regions, data='mean'):
    five_year = {}

    for r, df in regions.items():
        max_date = df['Date'].max()
        months = max_date.month

        end_date = max_date - relativedelta(months=int(months))
        start_date = end_date - relativedelta(years=5)

        df = df[(df['Date'] > start_date) & (df['Date'] <= end_date)]
        df = df.sort_values('Date')
        if data == 'mean':
            df = df.groupby(df['Date'].dt.month).mean()
        elif data == 'min':
            df = df.groupby(df['Date'].dt.month).min()
        elif data == 'max':
            df = df.groupby(df['Date'].dt.month).max()
        else:
            None

        five_year[r] = df

    return five_year


def merge_data(regions, region='Canada', product='Spec. propane'):
    maximum = five_year_average(regions, data='max')[region][product]
    minimum = five_year_average(regions, data='min')[region][product]
    average = five_year_average(regions, data='mean')[region][product]
    return [average, maximum, minimum]


def scrape_cer(remote=False):
    if mode == "prod":
        matplotlib.use("Agg")

    if remote:
        link = 'https://www.cer-rec.gc.ca/en/data-analysis/energy-commodities/natural-gas-liquids/statistics/YYYYlqdptrlmgs.xlsx'
        current_year = datetime.now().year
        current_link = link.replace('YYYY', str(current_year))
        print('retrieved remote data')
    else:
        current_link = "./2021lqdptrlmgs.xlsx"
        print('retrieved local data')

    try:
        df = pd.read_excel(current_link, sheet_name='Data')
    except:
        link_plus_one = link.replace('YYYY', str(current_year+1))
        df = pd.read_excel(link_plus_one, sheet_name='Data')

    # remove the french text and switch units to million barrels.
    df = df.rename(columns=english_only(df.columns))
    df = df.rename(columns={'Total butane': 'Butane'})
    df['Region'] = df['Region'].replace(english_only(df['Region'].unique()))
    df = change_units(df)
    regions = create_regions(df)
    return regions


def get_valid_years(regions, region, init=2):
    all_years = sorted(list(set([x.year for x in regions[region]['Date']])), reverse=True)
    if type(init) is list:
        selected_years = init
    else:
        selected_years = all_years[:init]
    return [[y, True] if y in selected_years else [y, False] for y in all_years]


def get_valid_product(products, new_product):
    for p in products:
        if p[0] == new_product:
            p[-1] = True
        else:
            p[-1] = False
    return products


def filter_data(regions, region='US Midwest', product='Spec. propane', year=2019):
    df = regions[region]
    df = df[df['Date'].dt.year == year]
    df = df.sort_values('Date')
    df = df.set_index('Date')[product]
    new_index = [x.month for x in df.index]
    df.index = new_index
    return df


def graph(regions,
          product='Spec. propane',
          region='Eastern Canada',
          lang='eng',
          years='init'):

    fiveYearAvgColor = CER['Forest']
    fiveYearRangeColor = CER['Ocean']

    if region == "Eastern Canada":
        title = "Ontario"
    elif region == "Western Canada":
        title = text['westernCanada'][lang]
    else:
        title = region

    def add_year_line(year, ax, color):
        yearLine = filter_data(regions, region, product, year=int(year))
        ax.plot(yearLine, linestyle='dashed', marker='o', label=str(year), color=color, linewidth=3.0)

    data = merge_data(regions, region, product)
    average, maximum, minimum = data[0], data[1], data[2]
    fig = plt.figure()
    fig = plt.figure(figsize=(15, 7), dpi=80)
    ax = fig.add_subplot(1, 1, 1)
    # 1) plot the five year average line
    ax.plot(average, label=text['5YearAvg'][lang], color=fiveYearAvgColor, linewidth=5.0)
    x = minimum.index
    # 2) plot the five year range
    ax.fill_between(x, minimum, maximum, alpha=0.4, color=fiveYearRangeColor, label=text['5YearRange'][lang])
    # 3) plot the year lines
    if years == "init":
        years = get_valid_years(regions, region)

    if len(years) > len(CER.values()):
        color_multiple = math.ceil(len(years)/len(CER.values()))
        all_colors = list(CER.values())*color_multiple
    else:
        all_colors = CER.values()

    lineColorList = [c for c in all_colors if c not in [fiveYearAvgColor, fiveYearRangeColor]]
    for colorIndex, y in enumerate(years):
        if y[-1]:
            add_year_line(y[0], ax, lineColorList[colorIndex])

    # set graph dimensions,etc
    ax.set_ylim(ymin=0)
    ax.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    ax.set_xticklabels(text['months'][lang])
    ax.legend(loc='lower right')
    # ax.legend(loc='best')
    ax.set_ylabel(text['millionbbl'][lang])
    plt.title(title)
    fig.savefig(os.path.join(script_dir, 'static', 'images', region.replace(' ', '')+'.png'))
    if mode == "dev":
        plt.show()


if __name__ == "__main__":
    regions = scrape_cer()
    graph(regions, product='Spec. propane', region='Canada', years="init")
    # all_graphs(regions,areas=['Eastern Canada','Western Canada'],lang='fra')
