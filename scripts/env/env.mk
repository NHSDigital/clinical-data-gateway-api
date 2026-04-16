.PHONY: env env-% _env

env:
	make _env

env-%: # Create .env file with environment variables - optional: name=[name of the environment, e.g. 'dev'] @Configuration
	make _env env="$*" # TODO: Implement difference envs

_env:
	scripts/env/env.sh "$(env)"

${VERBOSE}.SILENT: \
	_env \
	env \
	env-% \
