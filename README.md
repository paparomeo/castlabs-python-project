# castLabs Python Programming Task

castLabs HTTP proxy with JWT injection

## Requirements

The requirements for this project can be found [here](documentation/requirements.md).

## Development

### System components

#### Development

The following are the minimum system components required for developing this project:

- Python 3.8

#### Running / Testing

For ease of running/testing, the following system components are recommended:

- Make
- Docker Runtime
- Docker Compose

### Project automation

One of the implementation goals of this project was to automate _all_ the project development and deployment tasks.

For the tasks enumerated in the project requirements, this goal is achieved using [_Make_](https://en.wikipedia.org/wiki/Make_(software)). Both GNU and BSD variants should be supported by the supplied [Makefile](./Makefile).

Alternatively, improved project automated is provided with the help of the wonderful [_Invoke_](https://www.pyinvoke.org/).

To develop this project, having the Python 3 version of _Invoke_ installed is recommended and documentation pertaining local development will assume it is available. The author's preferred way to install _Invoke_ is as a system package:
- macOS: `brew install pyinvoke`
- Arch Linux: `pacman -S python-invoke`
- Ubuntu: `apt python3-invoke`

Alternatively it can also be installed with [`pipx`](https://pipxproject.github.io/pipx/) or using your favorite way of installing Python packages (you can follow the official instructions [here](https://www.pyinvoke.org/installing.html).

All the existing project automation tasks can be listed with the command:

```
inv --list
```

The help for each of the available tasks can be accessed with the command like (replace `<task_name>` with the name of the task):

```
inv <task_name> --help
```

### Virtual environment and dependency management

This project uses [_Poetry_](https://python-poetry.org/) to manage its virtual environment and Python package dependencies.

_Poetry_ can be installed by following the [official instructions](https://python-poetry.org/docs/#installation), and is a recommended dependency if you're developing this project.

A couple of `requirements.txt` files that can be consumed by `pip` have been generated from the Poetry lockfile, so Poetry is not a hard dependency for running and testing the project.

## Implementation

The most notable technologies used in the implementation of this project are:
- [Starlette](https://www.starlette.io/): lightweight ASGI framework/toolkit, which is ideal for building high performance asyncio services.
- [HTTPX](https://www.python-httpx.org/): fully featured HTTP client for Python 3, which provides sync and async APIs, and support for both HTTP/1.1 and HTTP/2.
- [authlib](https://authlib.org/): more specifically its RFC7519: JSON Web Token (JWT) support.
- [pytest](https://docs.pytest.org/): testing framework.
- [Uvicorn](https://www.uvicorn.org/): lightning-fast ASGI server.
- [Gunicorn](https://gunicorn.org/): Server / process manager (using Uvicorn workers).

## Build

The project's local virtual environment can be built using the command:

```
make build
```

## Running

⚠️ For the project to run and its tests to execute correctly the `JWT_SHARED_SECRET` environment variable **MUST** be defined. This can either be exported in the shell or, for simplicity sake, defined in a `.env` file in the project directory, where it will be accessible everywhere thet is is needed. This environment variable should contain a **hex encoded** byte string with the content of the share secret, an example of which can be found in the [requirements document](documentation/requirements.md), or a new one generated with the command:

```
python -c 'import secrets;print(secrets.token_bytes(64).hex())'
```

The port on which the service runs, in both the local and the containerized version of project, can be customized via the `HTTP_PORT` environment variable (but default the `8080` port is used).

### Locally

The local version of the project, can be run using the command (the virtual environment will be build if it doesn't exit yet):

```
make run
```

### Containerized

Running the containerized version of the project assumes a Docker Runtime and Docker Composed are available locally.

The number of workers started in the container can be configured using the `WORKERS` environment variable (by default it will `2 * CPU cores + 1`).

The containerized project can be run with the command:

```
make docker
```

The provided Docker container is based on Alpine Linux and therefore fairly lean, and the build dependencies have been removed from the image. 

## Testing

### Automated

This application has 💯 automated test code coverage. For simplicity sake, the automated tests depend on an active internet connection being available, since they make use of the [httpbin.org](https://httpbin.org/) service as an upstream. `httpbin` can easily be run locally as a container and that would be the implemented solution for better self-contained automated tests that don't have external dependencies.

The automated tests (with test coverage report) can be run using the command (the virtual environment will be build if it doesn't exit yet):

```
make test
```

### Manual

For manual testing, either start the local version of the service with `make run` or the containerized version of the project **with a single worker**, with `env WORKERS=1 make docker`. The single worker requirement is due to the state of the workers for the `/status` endpoint, for simplicity sake, being stored in memory and therefore being different from worker to worker (solutions for a production ready worker shared state are discussed in a later section of this document**.

⚠️ **Please note** that this proxy does _not_ support SSL (HTTPS) requests.

This proxy service _should_ support _any_ plain HTTP request. For example, the following commands will be successful and the correct inject of the `x-my-jwt` header can be verified in the response body, since `httpbin.org` returns a full copy of the request it received:

```
curl --proxy http://localhost:8080 http://httpbin.org/get
curl --proxy http://localhost:8080 --data "foo=bar" http://httpbin.org/post
curl --proxy http://localhost:8080 --header "Content-Type:application/json" --data '{"foo":"bar"}' http://httpbin
.org/post
curl --proxy http://localhost:8080 -X PUT http://httpbin.org/put
curl --proxy http://localhost:8080 -X DELETE http://httpbin.org/delete
curl --proxy http://localhost:8080 -X PATCH http://httpbin.org/patch
```

The status page, showing the seconds since service startup and the proxied requests count, can be browsed at http://localhost:8080/status

## Documentation

The code in conjunction with the automated tests and this document, _should_ provide all the necessary internal documentation for this project.

## Implementation

One of the goals of the implementation of this project was for the proxy to be as transparent as possible and be able to proxy _any_ plain HTTP request, independently of the HTTP verb or content encoding, while still adding the `x-my-jwt` header to all requests it proxied.

To achieve this goal, the author opted to use _Starlette_ simply as an [ASGI](https://asgi.readthedocs.io/en/latest/) toolkit, forsaking its full blown framework functionality. The code is therefore fairly low-level, directly handling the ASGI protocol, and transparently the request content unmodified, and only modifying the headers to add the `x-my-jwt` header.

There's logic to identify when a request is made directly to the service, rather than using it as proxy, so the `/status` endpoint can be correctly serviced.

The whole proxying and the service own endpoints logic is implemented asynchronously, courtesy of _Starlette_, and although the author didn't do any serious load testing, it _should_ perform well.

## TODO

Planed future improvements:

- Use Redis or Memcached to share state among the pool of workers.
- Go even lower level and use [Trio](https://trio.readthedocs.io/en/stable/) and [h11](https://github.com/python-hyper/h11) (and possibly [h2](https://github.com/python-hyper/hyper-h2) for HTTP/2 support), and implement the HTTP/1.1 proxying at the protocol level.
