from flask import Flask, render_template, request
from inventory_charts import scrape_cer, graph
app = Flask(__name__)


selected_region = 'Canada'


def on_load():
    print('scraping CER')
    regions = scrape_cer()
    graph(regions, region=selected_region)
    return regions


regions = on_load()


@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template("index.html",
                           region=selected_region,
                           my_list=regions.keys())


@app.route('/region', methods=['POST'])
def button():
    if request.method == "POST":
        new_region = request.form["region"]
        graph(regions, region=new_region)
        return render_template("index.html",
                               region=new_region.replace(" ", ""),
                               my_list=regions.keys())


if __name__ == '__main__':
    app.run(debug=True)
