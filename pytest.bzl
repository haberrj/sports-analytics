load("@rules_python//python:defs.bzl", _py_test = "py_test")


def pytest_test(name, srcs = [], deps = [], **kwargs):
    django_deps = [
        "//src/config",
        "//src/betting",
        "//src/fantasy",
        "//src/games",
        "//src/ingestion",
        "//src/players",
        "//src/predictions",
        "//src/stats",
        "//src/teams",
        "@pip//psycopg",
    ]

    extra_deps = [
        dep
        for dep in django_deps + ["@pip//pytest_django"]
        if dep not in deps
    ]

    _py_test(
        name = name,
        srcs = srcs + ["//src:pytest_main.py"],
        main = "//src:pytest_main.py",
        deps = deps + extra_deps,
        env = {
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "POSTGRES_HOST": "localhost",
        },
        **kwargs
    )