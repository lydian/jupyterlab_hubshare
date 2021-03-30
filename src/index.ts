import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { MainAreaPreviewWidget } from './preview';
import { requestAPI } from './handler';
import { Clipboard } from '@jupyterlab/apputils';

/**
 * Initialization data for the jupyterlab_hubshare extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_hubshare:plugin',
  autoStart: true,
  requires: [IFileBrowserFactory],
  activate: (app: JupyterFrontEnd, browser: IFileBrowserFactory) => {
    console.log('JupyterLab extension jupyterlab_hubshare is activated!');
    let mainAreaWidget: MainAreaPreviewWidget | null = null;
    const BASE_NAME = 'HubShare';
    const { tracker } = browser;

    app.commands.addCommand(`${BASE_NAME}:preview`, {
      caption: 'Preview Shared Notebook',
      execute: args => {
        if (mainAreaWidget !== null) {
          mainAreaWidget.close();
        }
        mainAreaWidget = new MainAreaPreviewWidget(
          String(args.path),
          String(args.name),
          (path: string) => {
            console.log(path);
            app.commands.execute(`${BASE_NAME}:import`, { path });
          }
        );
        if (!mainAreaWidget.isAttached) {
          app.shell.add(mainAreaWidget, 'main');
        }
        app.shell.activateById(mainAreaWidget.id);
      }
    });

    app.commands.addCommand(`${BASE_NAME}:import`, {
      caption: 'import notebook',
      execute: args => {
        const path = String(args.path);
        requestAPI<any>('content', {
          method: 'PUT',
          body: JSON.stringify({ path })
        }).then(data => {
          const browserPath = browser.defaultBrowser.model.path;
          return new Promise(resolve => {
            app.commands
              .execute('docmanager:new-untitled', {
                path: browserPath,
                type: 'notebook'
              })
              .then(model => {
                mainAreaWidget.close();
                return app.commands.execute('docmanager:open', {
                  factory: 'Notebook',
                  path: model.path
                });
              })
              .then(widget => {
                return widget.context.ready.then(() => {
                  widget.model.fromJSON(data.content);
                  resolve(widget);
                });
              })
              .then(() => {
                return app.commands.execute('docmanager:save');
              });
          });
        });
      }
    });

    app.commands.addCommand(`${BASE_NAME}:share-link`, {
      label: 'Copy Sharable link',
      execute: () => {
        const widget = tracker.currentWidget;
        if (!widget) {
          return;
        }
        const path = widget.selectedItems().next().path;
        console.log(path);
        requestAPI<any>('share-url', {
          method: 'PUT',
          body: JSON.stringify({ path })
        }).then(data => {
          let url = data.share_path as string;
          console.log(data);
          if (!url.startsWith('http://') || !url.startsWith('https://')) {
            url = new URL(url, window.location.href).href;
          }
          console.log(url);
          Clipboard.copyToSystem(url);
        });
      },
      iconClass: 'jp-MaterialIcon jp-LinkIcon'
    });

    app.contextMenu.addItem({
      command: `${BASE_NAME}:share-link`,
      selector: '.jp-DirListing-item[data-file-type="notebook"]',
      rank: 3
    });

    const params = new URLSearchParams(window.location.search);
    if (params.get('hubshare-preview')) {
      console.log(`original path: ${params.get('hubshare-preview')}`);
      const path = params.get('hubshare-preview');
      const name = atob(path).split('/').pop();
      console.log(`Found preview path: ${path}`);
      Promise.all([app.restored]).then(() => {
        app.commands.execute(`${BASE_NAME}:preview`, { path, name });
      });
    }
  }
};

export default extension;
