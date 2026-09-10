from sies_musica.texto import normalizar_nombre


def test_minusculas_sin_tildes():
    assert normalizar_nombre("Composición Musical") == "composicion musical"


def test_capitalizacion_y_espacios():
    assert normalizar_nombre("  Pedagogía EN Música ") == "pedagogia en musica"


def test_tilde_n_y_u():
    assert normalizar_nombre("CÓDIGO CARRERA Ñ") == "codigo carrera n"


def test_ya_normalizado():
    assert normalizar_nombre("composicion musical") == "composicion musical"


def test_con_guiones_se_mantienen():
    assert normalizar_nombre("Música y Sonido") == "musica y sonido"


def test_multiples_espacios_internos():
    assert normalizar_nombre("Técnico   en  Sonido") == "tecnico en sonido"
