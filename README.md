# Write and Call Rust from Python
We often do calculations in Python that depend on systems-language level performance. Think Numpy arrays. These calculations pipe down to C binaries and then surface back up to python. Rust, C++, C, are all good languages to implement machine-code level looping and easily call from python. For a variaty of reasons Rust is my go-to when the situation allows. Wiring up a rust code-base to python and then packaging and including the rust binaries with your distribution is not difficult at all, but I thought a tutorial here might be helpful, as it can be just a bit finicky. 

Because I am a Python developer, Rust is usually something I layer onto my project, so that is how I will present this. Let's start with an existing Python project. The minimal pyproject.toml looks like this:

```toml
[project]
name = "pimulator"
version = "0.1.0"
requires-python = ">=3.14"
```
>[!NOTE]
>If you don't use `pyproject.toml`, you will need to add it to the root of your project. Otherwise you will not be able to configure `maturin` tutorial.

>[!TIP] 
> You can access the [pimulator GitHub repo](https://github.com/iamorlando/pimulator) to see the fully built out example for a minimal Python/Rust mixed project. I built Pimulator specifically to show how one wires up Rust into Python. The project approximates Pi by naiviely sampling a circle with pseudo-random numbers. It implements this approach in rust and in python and lets you compare the performance aspects of this exercise. You can see how the results of this comparison in [this notebook](https://github.com/iamorlando/pimulator/blob/main/notebooks/comparisons.ipynb).

## Maturin
Maturin is a tool that makes the Python/Rust interop possible. It builds your Rust into a binary. If you plan on publishing your Python via wheels rather than sharing your source, then Maturin will also bind the Rust binary into the wheel.

### 1. Install Maturin in Your Python Environment
>[!IMPORTANT]For the purposes of this tutorial you will want to work within a virtual environment. I will use standard python cli commands, however you might need to adapt my `pip install`s to `poetry add`s and so forth.
<br/>
Install maturin
```bash
pip install maturin
```

### 2. Modify `pyproject.toml` to Build Using Maturin
Add this to `pyproject.toml`
```toml
[build-system]
requires = ["maturin>=1.10,<2.0"]
build-backend = "maturin"
```

### 3. Configure Maturin
Finally we add this to `pyproject.toml`
```toml
[tool.maturin]
module-name = "pimulator.rust"
bindings = "pyo3"
```
`module-name` here refers to the name Python will see for the compiled Rust binaries. `pimulator.rust` means our import in Python will look like:
```python
from pimulator.rust import foo
```

## Set Up  Your Library
> [!IMPORTANT]
>If you haven't yet installed Rust, then you can do so easily by following [this guide](https://doc.rust-lang.org/book/ch01-01-installation.html). 

Back to our Rust library. Create a directory inside your python project where you will keep your Rust code. I like to name this directory: `rust`. In it you typically find project files and all the source code within a directory called `src`. Because we are setting up a Rust `library` within our Python project, we will need to have a file called `rust/src/lib.rs` exporting our source code. Lets set that up now.
```bash
mkdir -p rust/src
touch rust/src/lib.rs
```

Place this example in `rust/src/lib.rs`:
```rust
use pyo3::prelude::*;

#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pymodule]
fn rust(// This must be named `rust` to match `module-name = "pimulator.rust"`.
_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}

```

>[!TIP]
>The [GitHub repo](https://github.com/iamorlando/pimulator) for this tutorial creates multiple modules that are visible to Python. It is more representative of a real project setup and you may find it to be a helpful reference later on.

### Cargo
To finish setting up Rust in our once pure-Python project we add our `Cargo.toml` file. This is essentially Rust's `pyproject` equivalent. It will list all the dependencies you install for your Rust library, and has some amazing features. For example, if you want to see docs for all your dependencies, you can run `cargo doc --open`. I like to place `Cargo.toml` at the root of my project even though the standard setup is to put it inside the `rust` directory. This means we need to tell `maturin` to look for `Cargo.toml` in the project root. 
<br/>
Update `pyproject.toml`

```toml
[tool.maturin]
module-name = "pimulator.rust"
bindings = "pyo3"
manifest-path = "Cargo.toml" # <- add this
```

In the root of your project add `Cargo.toml`
```bash
touch Cargo.toml
```

Place this configuration in your `Cargo.toml`
```toml
[package]
name = "pimulator"
version = "0.1.0"
edition = "2024"

[lib]
name = "rust"
path = "rust/src/lib.rs"
crate-type = ["cdylib"]

[dependencies]
pyo3 = "0.27.0"
```
The above is the minimum required set of keys. The name `rust` refers to the main module you are exporting in your Rust library. The package name is set to pimulator. This means that Cargo will build your library and expose it as `pimulator.rust`, which matches what we said we wanted in the `[tool.maturin]` section of `pyproject.toml` .

### Building the Binaries
To make coding in Rust seamless and ergonomical, it would be nice if each time we change the Rust code we have that reflected in our Python. To do this we use `cargo-watch`. I personally don't like writing this command each time I start coding, so I use a MakeFile, it looks like this:

```make
VENV := .venv
PY   := $(VENV)/bin/python
watch:
	cargo install cargo-watch && cargo watch -C . -w rust/src -w Cargo.toml --ignore target -s "$(PY) -m maturin develop"
release:
	$(PY) -m maturin build --release --out ./dist
```
With this MakeFile you would watch the `rust` folder with
```bash
make watch
```
Now every time you save a Rust file the binary will be quickly rebuilt and your testing will pick up your latest Rust code.

If you want to publish your code you can use the wheel created with
```bash
make release
```
Make sure you build the right wheel for the right target. Maturin automatically generates an architecture/target matrix which you can copy paste into a GitHub Actions workflow. You can generate it with:
```bash
maturin generate-ci github
```
That's it! To conclude lets summarize the files we added and our project structure.

## Summary

### `Project Structure`
```bash
.
├── Cargo.toml
├── MakeFile
├── pimulator
│   ├── __init__.py
├── pyproject.toml
└── rust
    └── src
        ├── lib.rs
```

### `pyproject.toml`
```toml
[project]
name = "pimulator"
version = "0.1.0"
description = ""
requires-python = ">=3.14"

[build-system]
requires = ["maturin>=1.10,<2.0"]
build-backend = "maturin"

[tool.maturin]
bindings = "pyo3"
module-name = "pimulator.rust"
manifest-path = "Cargo.toml"

```

### `Cargo.toml`
```toml
[package]
name = "pimulator"
version = "0.1.0"
edition = "2024"

[lib]
name = "rust"
path = "rust/src/lib.rs"
crate-type = ["cdylib"]

[dependencies]
pyo3 = "0.27.0"

```

### `rust/src/lib.rs`
```rust
use pyo3::prelude::*;

#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}


#[pymodule]
fn rust(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
```

### `pimulator/__init__.py`
```python
from pimulator.rust import sum_as_string
```

### `MakeFile`
```make
VENV := .venv
PY   := $(VENV)/bin/python
watch:
	cargo install cargo-watch && cargo watch -C . -w rust/src -w Cargo.toml --ignore target -s "$(PY) -m maturin develop"
release:
	$(PY) -m maturin build --release --out ./dist
```

And that's all there is to it! You've now wired up Rust functions to your Python library. Test it in a notebook or in the terminal with
```bash
python -c "from pimulator import sum_as_string;print(sum_as_string(1,2))"
```
