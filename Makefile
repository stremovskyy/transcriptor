# Variables
IMAGE_NAME = stremovskyy/transcriptor
VERSION = latest
PLATFORMS = linux/amd64,linux/arm64

# Build locally for the host architecture
build:
	docker build -t $(IMAGE_NAME):$(VERSION) .

# Build for multiple architectures using Buildx
buildx:
	docker buildx build --platform $(PLATFORMS) -t $(IMAGE_NAME):$(VERSION) --load .

# Push the image to Docker Hub
push:
	docker push $(IMAGE_NAME):$(VERSION)

# Build and push multi-architecture image
deploy:
	docker buildx build --platform $(PLATFORMS) -t $(IMAGE_NAME):$(VERSION) --push .

# Test the container locally
run:
	docker run -d -p 8080:8080 --env-file .env $(IMAGE_NAME):$(VERSION)

# Clean up local images
clean:
	docker rmi $(IMAGE_NAME):$(VERSION)
