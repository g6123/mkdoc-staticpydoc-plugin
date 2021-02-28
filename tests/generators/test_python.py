from yaarg.generators.parso import ParsoGenerator


def test_generate():
    # Given
    generator = ParsoGenerator()
    options = generator.validate_options({})

    # When
    output = generator.generate(
        "/mnt/data/Development/mkdocs-yaarg-plugin/yaarg/generators/base.py",
        symbol=None,
        options=options,
    )

    # Then
    pass
