import React from 'react';

import { MainAreaWidget, ReactWidget } from '@jupyterlab/apputils';
import { ServerConnection } from '@jupyterlab/services';
import { URLExt } from '@jupyterlab/coreutils';
/**
 * Interface describing component properties.
 *
 * @private
 */

class PreviewWidget extends ReactWidget {
  importFunc: any;
  name: string;
  path: string;

  constructor(path: string, name: string, importFunc: any) {
    super();
    this.name = name;
    this.path = path;
    this.importFunc = importFunc;
  }
  render(): JSX.Element {
    const settings = ServerConnection.makeSettings();
    const encodedPath = encodeURIComponent(this.path);
    const requestUrl = URLExt.join(
      settings.baseUrl,
      'jupyterlab_hubshare',
      `preview?path=${encodedPath}`
    );
    return (
      <div style={{ width: '100%', height: '100%' }}>
        <div>
          <input
            type="button"
            value="Import"
            onClick={() => this.importFunc(this.path)}
          />
        </div>
        <iframe style={{ width: '100%', height: '100%' }} src={requestUrl} />
      </div>
    );
  }
}

export class MainAreaPreviewWidget extends MainAreaWidget {
  path: string;
  name: string;

  constructor(path: string, name: string, importFunc: (path: string) => void) {
    super({ content: new PreviewWidget(path, name, importFunc) });
    this.id = 'HubShare-preview';
    this.title.label = `Preview: ${name}`;
    this.title.closable = true;
  }
}
