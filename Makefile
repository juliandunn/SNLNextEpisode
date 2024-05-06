pkg: clean
	pip install --target ./package boto3
	pip install --target ./package ask-sdk-core
	pip install --target ./package requests
	cd package && zip -r ../SNLNextEpisode.zip . && cd ..
	zip SNLNextEpisode.zip lambda_function.py

clean:
	rm SNLNextEpisode.zip || true
	rm -rf package