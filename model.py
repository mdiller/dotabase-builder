from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from start import app

db = SQLAlchemy(app)

class Hero(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(128))
    localized_name = db.Column(db.String(128))
    img_path = db.Column(db.String(128))
    icon_path = db.Column(db.String(128))

    base_health_regen = db.Column(db.Float)
    base_movement = db.Column(db.Integer)
    turn_rate = db.Column(db.Float)
    base_armor = db.Column(db.Integer)
    attack_range = db.Column(db.Integer)
    attack_projectile_speed = db.Column(db.Integer)
    attack_damage_min = db.Column(db.Integer)
    attack_damage_max = db.Column(db.Integer)
    attack_rate = db.Column(db.Float)
    attack_point = db.Column(db.Float)
    attr_primary = db.Column(db.String(3))
    attr_base_strength = db.Column(db.Integer)
    attr_strength_gain = db.Column(db.Float)
    attr_base_intelligence = db.Column(db.Integer)
    attr_intelligence_gain = db.Column(db.Float)
    attr_base_agility = db.Column(db.Integer)
    attr_agility_gain = db.Column(db.Float)


class Item(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(128))
    localized_name = db.Column(db.String(128))
    cost = db.Column(db.Integer)
    recipe = db.Column(db.Boolean)
    secret_shop = db.Column(db.Boolean)
    side_shop = db.Column(db.Boolean)
    img_path = db.Column(db.String(128))
