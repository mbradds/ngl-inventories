from flask import Flask, render_template, request
from inventory_charts import scrape_cer, graph, get_valid_years
app = Flask(__name__)


selected_region = "Canada"
current_units = "Million barrels"


def on_load():
    # print('scraping CER')
    regions = scrape_cer()
    graph(regions, region=selected_region, years="init")
    return regions


regions = on_load()
form_years = get_valid_years(regions, selected_region, init=2)


def year_selection(new_years, regions):
    return get_valid_years(regions, selected_region, init=new_years)


@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template("index.html",
                           region=selected_region,
                           region_list=regions.keys(),
                           year_list=form_years)


@app.route('/region', methods=['POST'])
def button():
    if request.method == "POST":
        new_region = request.form["region"]
        new_years = [int(x) for x in request.form.getlist("year")]
        form_years = year_selection(new_years, regions)
        graph(regions, region=new_region, years=form_years)
        return render_template("index.html",  # TOOD: change this from "index.html" to something like "image.html" and only reload part of the page!
                               region=new_region,  # .replace(" ", ""),
                               region_list=regions.keys(),
                               year_list=form_years)


if __name__ == '__main__':
    app.run(debug=True)
