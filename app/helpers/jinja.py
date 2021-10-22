from app.__main__ import app


@app.template_filter('app_config')
def filter_app_config(x, default=None):

	return app.config.get(x, default)
