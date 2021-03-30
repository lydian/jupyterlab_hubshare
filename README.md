# jupyterlab_hubshare

![Github Actions Status](https://github.com/lydian/jupyterlab_hubshare/workflows/Build/badge.svg)
[![codecov](https://codecov.io/gh/lydian/jupyterlab_hubshare/branch/master/graph/badge.svg)](https://codecov.io/gh/lydian/jupyterlab_hubshare)

share notebooks on jupyterhub

![JupyterHub-share-demo-_1_](https://user-images.githubusercontent.com/678485/112790349-03a7b400-9014-11eb-9ef4-ad8072614b50.gif)



This extension is composed of a Python package named `jupyterlab_hubshare`
for the server extension and a NPM package named `jupyterlab_hubshare`
for the frontend extension.

## Sharing

In general, there will be multiple use case when using jupyterhub:


## Requirements

* JupyterLab >= 3.0

## Install

```bash
pip install jupyterlab_hubshare
```

## Configuration
The extension supports multiple use cases:

### Use Case 1: All users on jupyterhub share the same Interface
In this scenario, the path for user A and user B are exactly the same, therefore we only need to configure the URL

```python
c.HubShare.file_path_template = "{path}"
```
This will make the sharable link looks like http://your.jupyter/user-redirect/?hubshare-preview=path/to/ipynb

if you prefer directly access the file, you can also add:
```
c.HubShare.use_preview = False
```
this will make the sharable link looks like http://your.jupyter/user-redirect/path/to/ipynb

but please be aware that this will allow other user directly modify the same file, which should be avoided in most cases.

### Use Case 2: User have their own work space but can still access others workspace
This is honestly my preferable settings, for example:

- userA work space: `path/workspaces/userA/`
- userB work space: `path/workspaces/userB/`
- but both userA and userB have a `shortcut` folder links to `path/workspaces/` so that they can still check others workspaces.

In this case, you can configure that with:
```python
c.HubShare.file_path_template = "shortcut/{user}/{path}"
```
This will make the shareable link looks like http://your.jupyter/user-redirect/?hubshare-preview=shortcut/userA/path/to/ipynb
(if sharing userA's notebook)

Similarly, you can also set
```python
c.HubShare.use_preview = False
```
This will make the sharable link looks like http://your.jupyter/user-redirect/shortcut/userA/path/to/ipynb
Same as above, be aware that this will allow the other user directly modify the same file!
### Use Case 3: User have their own work space, and they are unable to directly reach to others workspace
This is much more like the previous scenario, but there's no `shortcut` folder to give access to other folder.
In this case, you will need to also configure the contents_manager:
```python
c.HubShare.contents_maanger = {
    "manager_cls": FileContentManager,
    "kwargs": {
        "root_dir": "path/to/workspaces/
    }
}
c.HubShare.file_path_template = "{user}/{path}"
```
This will create a sharable link looks like:
This will make the shareable link looks like http://your.jupyter/user-redirect/?hubshare-preview=userA/path/to/ipynb
(if sharing userA's notebook)

Note that given that the current contents manager doesn't have access to other users workspaces, setting `use_preview=False` will make invalid link.


## Troubleshoot

If you are seeing the frontend extension, but it is not working, check
that the server extension is enabled:

```bash
jupyter server extension list
```

If the server extension is installed and enabled, but you are not seeing
the frontend extension, check the frontend extension is installed:

```bash
jupyter labextension list
```


## Contributing

### Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the jupyterlab_hubshare directory
# Install package in development mode
pip install -e .
# Link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite
# Rebuild extension Typescript source after making changes
jlpm run build
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm run watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).

By default, the `jlpm run build` command generates the source maps for this extension to make it easier to debug using the browser dev tools. To also generate source maps for the JupyterLab core extensions, you can run the following command:

```bash
jupyter lab build --minimize=False
```

There's also a quick target in Makefile:
```bash
make venv
```
build the workspace
```bash
make build
```
build the package
```bash
make watch
```
to quickly develop with jupyterlab
```bash
make jupyterhub
```
to test the share function in jupyterhub


### Uninstall

```bash
pip uninstall jupyterlab_hubshare
```
