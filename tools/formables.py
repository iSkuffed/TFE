"""TFE's changes to vanilla's formable countries, applied by borders.bar_empires_from_formables (which writes the file).

Edit the changes here, then `python tools/borders.py`; never the .txt. tools/test_formables.py states what they must do.
"""
import re


def tokens(text):
    return re.findall(r"[{}=]|[^\s{}=]+", re.sub(r"#.*", "", text))


def definitions(path):
    """name -> (top-level continent, its locations), for every continent, region, area and province of vanilla's map."""
    toks = tokens(path.read_text(encoding="utf-8-sig"))
    info = {}

    def walk(i, top):
        locs = []
        while toks[i] != "}":
            if toks[i + 1] == "=" and toks[i + 2] == "{":
                name = toks[i]
                sub, i = walk(i + 3, top)
                info[name] = (top, sub)
                locs += sub
            elif toks[i + 1] == "=":
                i += 3  # `not_eligible_for_dynamic_country_name = yes`
            else:
                locs.append(toks[i])
                i += 1
        return locs, i + 1

    i = 0
    while i < len(toks):
        top = toks[i]
        sub, i = walk(i + 3, top)
        info[top] = (top, sub)
    return info


def close_of(text, j):
    """index just past the brace that closes the block whose `{` was just before j."""
    depth = 1
    while depth:
        if text[j] == "#":
            j = text.index("\n", j)
            continue
        depth += (text[j] == "{") - (text[j] == "}")
        j += 1
    return j


def blocks(text):
    """(key, start, end) of each top-level `X_f = { ... }`."""
    return [(m.group(1), m.start(), close_of(text, m.end())) for m in re.finditer(r"^(\w+_f) = \{", text, re.M)]


def sub(body, key):
    m = re.search(rf"^\t{key} = \{{(.*?)^\t\}}", body, re.M | re.S)
    return re.sub(r"#.*", "", m.group(1)) if m else ""


def land(body, defs):
    """the locations a formable requires."""
    locs = set()
    for key in ("continents", "sub_continents", "regions", "areas", "provinces", "locations"):
        for n in sub(body, key).split():
            locs |= set(defs[n][1]) if n in defs else {n}
    return locs


def in_europe(body, defs):
    """most of its required land is on vanilla's europe continent (Rome and Byzantium count; the Mongols do not)."""
    here, europe = land(body, defs), set(defs["europe"][1])
    return bool(here) and len(here & europe) * 2 > len(here)


GATE = "has_tribal_government = no\t# TFE"

EDITS = [
    # no Netherlands
    ("""		NOR = { tag = WRE tag = EAR tag = JIN }	# TFE
		culture = { has_culture_group = culture_group:netherlandish_group }
""", """		NOR = { tag = WRE tag = EAR tag = JIN }	# TFE
		always = no	# TFE: the Netherlands is never formable
		culture = { has_culture_group = culture_group:netherlandish_group }
"""),
    # Portugal, a Kingdom of both its areas
    ("""POR_f = { # Portugal
	level = 2
	required_locations_fraction = 0.75
	rule = historical

	potential = {
		NOR = { tag = WRE tag = EAR tag = JIN }	# TFE
		NOT = { tag = POR }
		culture = culture:portuguese
		religion.group = religion_group:christian
	}

	allow = {
	}
""", """POR_f = { # Portugal
	level = 3	# TFE: a Kingdom
	required_locations_fraction = 0.6	# TFE
	rule = historical

	potential = {
		NOR = { tag = WRE tag = EAR tag = JIN }	# TFE
		NOT = { tag = POR }
	}

	allow = {
		current_age = age_6_revolutions	# TFE: the Age of Charlemagne; the County of Portugal dates from 868
	}
"""),
    ("""	areas = {
		north_portugal_area
	}

	form_effect = {
	}
}
""", """	areas = {
		north_portugal_area
		south_portugal_area	# TFE
	}

	form_effect = {
		# TFE
		if = {
			limit = { country_rank_level < 3 }
			set_country_rank_effect = { rank = country_rank:rank_kingdom }
		}
	}
}
"""),
    # Germany becomes Germania, a Kingdom
    ("""GER_f = {

	level = 4
""", """GER_f = {

	level = 3	# TFE: Germania is a Kingdom
"""),
    ("""	form_effect = {
		if = {
			limit = { country_rank_level < 4 }
			set_country_rank_effect = { rank = country_rank:rank_empire }
		}
	}
}

HRE_f""", """	form_effect = {
		if = {
			limit = { country_rank_level < 3 }	# TFE
			set_country_rank_effect = { rank = country_rank:rank_kingdom }	# TFE
		}
	}
}

HRE_f"""),
    # the Holy Roman Empire, no longer waiting on an organisation that does not exist yet
    ("""	required_locations_fraction = 0.75
	rule = plausible
	potential = {
		NOR = { tag = WRE tag = EAR tag = JIN }	# TFE
		exists = international_organization:hre
		is_member_of_international_organization = international_organization:hre
	}

	allow = {
		custom_tooltip = {
			text = HRE_f_tt
			always = no
		}
	}
""", """	required_locations_fraction = 0.6	# TFE
	rule = plausible
	potential = {
		NOR = { tag = WRE tag = EAR tag = JIN }	# TFE
		religion.group = religion_group:christian	# TFE: the *Holy* Roman Empire
	}

	allow = {
	}
"""),
    ("""	regions = {
		north_german_region
		south_german_region
	}
	form_effect = {
	}
}

MOL_f""", """	regions = {
		north_german_region
		south_german_region
		france_region	# TFE
	}
	form_effect = {
		# TFE
		if = {
			limit = { country_rank_level < 4 }
			set_country_rank_effect = { rank = country_rank:rank_empire }
		}
	}
}

MOL_f"""),
]


def tfe_formables(text, defs):
    """vanilla's formables (already barred to the empires) with TFE's: the edits above, then no tribe forms a European nation."""
    for old, new in EDITS:
        assert text.count(old) == 1, f"formables: vanilla changed, carry over this edit by hand:\n{old}"
        text = text.replace(old, new)
    for key, start, end in reversed(blocks(text)):
        body = text[start:end]
        if not in_europe(body, defs):
            continue
        allow = re.search(r"^\tallow = \{[ \t]*\n", body, re.M)
        if allow:   # the closing brace is on its own line in every vanilla entry
            at = body.index("\n\t}", allow.end() - 1) + 1
            body = body[:at] + "\t\t" + GATE + "\n" + body[at:]
        else:       # no allow: add one after the potential block
            pot = re.search(r"^\tpotential = \{", body, re.M)
            eol = body.index("\n", close_of(body, pot.end())) + 1
            body = body[:eol] + "\n\tallow = {\n\t\t" + GATE + "\n\t}\n" + body[eol:]
        text = text[:start] + body + text[end:]
    return text
