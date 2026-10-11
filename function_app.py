import json
import logging
import urllib.parse

import azure.functions as func

from geo import search_places
from kundli_service import build_chart, build_transit_for, current_place_fields, current_place_query, parse_birth_form
from kundli_store import get_store
from pages import render_page

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

_store = None


def store():
    global _store
    if _store is None:
        _store = get_store()
    return _store


def html_response(body, status=200):
    return func.HttpResponse(body, status_code=status, mimetype="text/html", charset="utf-8")


def redirect(location):
    return func.HttpResponse(status_code=303, headers={"Location": location})


# The Functions host can't route "" to the site root, and a catch-all shadows other
# GET routes, so all GETs come through here and are dispatched on the path.
@app.route(route="{*path}", methods=["GET"])
def get_dispatch(req: func.HttpRequest) -> func.HttpResponse:
    path = (req.route_params.get("path") or "").strip("/")
    if path == "":
        return index(req)
    if path == "api/places":
        return places(req)
    return func.HttpResponse("Not found", status_code=404)


def index(req: func.HttpRequest) -> func.HttpResponse:
    kundli_id = req.params.get("id")
    chart_html, transit_html, form, error = "", "", None, ""
    if kundli_id:
        rec = store().get(kundli_id)
        if rec is None:
            return redirect("/")
        chart_html, form = build_chart(rec), {**rec, **current_place_fields(req.params)}
        try:
            transit_html = build_transit_for(rec, req.params)
        except ValueError as e:
            error = str(e)
    return html_response(render_page(store().list(), kundli_id, chart_html, form, error, transit_html))


@app.route(route="kundli", methods=["POST"])
def create_kundli(req: func.HttpRequest) -> func.HttpResponse:
    form = req.form
    try:
        rec = parse_birth_form(form)
        chart_html = build_chart(rec)
        transit_html = build_transit_for(rec, form)
    except ValueError as e:
        return html_response(render_page(store().list(), form=dict(form), error=str(e)), status=400)

    if form.get("save"):
        kundli_id = store().add(rec)
        return redirect("/?id=" + urllib.parse.quote(kundli_id) + current_place_query(form))
    return html_response(render_page(store().list(), chart_html=chart_html, form={**rec, **current_place_fields(form)},
                                     transit_html=transit_html))


@app.route(route="kundli/{id}/delete", methods=["POST"])
def delete_kundli(req: func.HttpRequest) -> func.HttpResponse:
    store().delete(req.route_params["id"])
    return redirect("/")


def places(req: func.HttpRequest) -> func.HttpResponse:
    q = (req.params.get("q") or "").strip()
    if len(q) < 2:
        return func.HttpResponse("[]", mimetype="application/json")
    try:
        results = search_places(q)
    except Exception:
        logging.exception("Place lookup failed for %r", q)
        return func.HttpResponse("[]", status_code=502, mimetype="application/json")
    return func.HttpResponse(json.dumps(results, ensure_ascii=False), mimetype="application/json", charset="utf-8")
