from os import path
from collections import defaultdict
import csv, json

from flask import Flask, render_template
from flask_frozen import Freezer
from citations import CitationLoader


template_folder = path.abspath('./wiki')
cdn_url = "https://static.igem.wiki/teams/4615/wiki/"

citation_loader = CitationLoader("bibtex.bib")

app = Flask(__name__, template_folder=template_folder)
app.url_map.charset = 'utf-8'
#app.config['FREEZER_BASE_URL'] = environ.get('CI_PAGES_URL')
app.config['FREEZER_DESTINATION'] = 'public'
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True
freezer = Freezer(app)

"""Load the navigation bar from a file."""
with open("navigation.json") as f:
    navigation = json.load(f)
    for obj in navigation:
        if "sublinks" in obj:
            obj["sublinks"] = [(x["text"], x["text"].lower().replace(" ", "-") \
                                if not "link" in x else x["link"]) for x in obj["sublinks"]]
        elif "link" not in obj:
            obj["link"] = obj["text"].lower().replace(" ", "-")

@app.cli.command()
def freeze():
    freezer.freeze()

@app.cli.command()
def serve():
    freezer.run()

def subpages_skeleton():
    subpages = []
    def ensure_subpage():
        if len(subpages) == 0:
            subpages.append({ "heading": "", "key": "", "subheadings": []})

    d = { "pages": [], "subpages": subpages, "ensure_subpage": ensure_subpage, "print": print }

    def set_page(page_name):
        d["pages"].append(page_name)

    d["set_page"] = set_page

    d["citer"] = citation_loader.citer()
    d["reset_citer"] = d["citer"].reset
    
    return d

@app.route('/')
def home():
    return render_template('pages/home.html',
                           cdn=lambda x: cdn_url + x,
                           **subpages_skeleton(),
                           navigation=navigation)

@app.route("/people")
def peopl():
    team_members = defaultdict(list)
    team_members["President"] = []
    team_members["Wet Lab"] = []
    team_members["Dry Lab"] = []
    team_members["Human Practices"] = []
    team_members["Hardware"] = []
    with open("static/team.csv", newline="") as f:
        reader = csv.reader(f)
        for line in reader:
            if line[0] == "Name" or line[0] == "":
                continue
            member = {}
            member["name"] = line[0]
            member["role"] = line[1]
            member["description"] = line[2]
            member["linkedin"] = line[4]
            member["website"] = line[5]
            member["email"] = line[6]
            member["priority"] = 0

            image_key = line[0].split()[0].lower()
            member["picture"] = image_key + ".png"

            lower_role =  member["role"].split(", ")[0].lower()
            group = team_members[lower_role.replace("lead", "").replace("director", "").strip().title()]

            if "director" in lower_role:
                member["priority"] = 10
            elif "lead" in lower_role:
                member["priority"] = 5
            
            group.append(member)

    for group in team_members.values():
        group.sort(key=lambda x: x["priority"], reverse=True)

    return render_template('pages/people.html',
                           cdn=lambda x: cdn_url + x,
                           team_members=team_members,
                           **subpages_skeleton(),
                           navigation=navigation)

@app.route('/<page>')
def pages(page):
    subpages = subpages_skeleton()
    return render_template("pages/" + page.lower() + '.html',
                        cdn=lambda x: cdn_url + x,
                        **subpages,
                        navigation=navigation)

# Main Function, Runs at http://0.0.0.0:8080
if __name__ == "__main__":
    app.run(port=3000, debug=True)