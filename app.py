"""Flask app for self-hosting with gunicorn. Same pages and routes as function_app.py."""
import logging
import os

from flask import Flask, Response, jsonify, redirect, request, url_for

from geo import search_places
from kundli_service import build_chart, build_transit_for, current_place_fields, current_place_query, parse_birth_form
from kundli_store import get_store
from pages import render_page

# The systemd unit points this at /var/lib/kundli; default to a file in the working dir
os.environ.setdefault("KUNDLI_DB", "kundli.db")

app = Flask(__name__)
store = get_store()


def html_response(body, status=200):
    return Response(body, status=status, mimetype="text/html")


@app.get("/")
def index():
    kundli_id = request.args.get("id")
    chart_html, transit_html, form, error = "", "", None, ""
    if kundli_id:
        rec = store.get(kundli_id)
        if rec is None:
            return redirect("/", code=303)
        chart_html, form = build_chart(rec), {**rec, **current_place_fields(request.args)}
        try:
            transit_html = build_transit_for(rec, request.args)
        except ValueError as e:
            error = str(e)
    return html_response(render_page(store.list(), kundli_id, chart_html, form, error, transit_html))


@app.post("/kundli")
def create_kundli():
    form = request.form
    try:
        rec = parse_birth_form(form)
        chart_html = build_chart(rec)
        transit_html = build_transit_for(rec, form)
    except ValueError as e:
        return html_response(render_page(store.list(), form=form.to_dict(), error=str(e)), status=400)

    if form.get("save"):
        kundli_id = store.add(rec)
        return redirect(url_for("index", id=kundli_id) + current_place_query(form), code=303)
    return html_response(render_page(store.list(), chart_html=chart_html, form={**rec, **current_place_fields(form)},
                                     transit_html=transit_html))


@app.post("/kundli/<kundli_id>/delete")
def delete_kundli(kundli_id):
    store.delete(kundli_id)
    return redirect("/", code=303)


@app.get("/api/places")
def places():
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify([])
    try:
        return jsonify(search_places(q))
    except Exception:
        logging.exception("Place lookup failed for %r", q)
        return jsonify([]), 502


@app.get("/healthz")
def healthz():
    return "ok"
