import zipfile
from pathlib import Path

import httpx
import llm
import yaml
from rich import print


def str_presenter(dumper, data):
    # from: https://github.com/yaml/pyyaml/issues/240
    # Remove any trailing spaces messing out the output.
    block = '\n'.join([line.rstrip() for line in data.splitlines()])
    if data.endswith('\n'):
        block += '\n'
    return dumper.represent_scalar('tag:yaml.org,2002:str', block, style='|')


def write_llm_templates(base_dir):
    templates_dir = llm.user_dir() / 'templates'
    # Loop through each subdirectory in the base directory
    for subdir in base_dir.iterdir():
        system_md_path = subdir / 'system.md'

        # Check if it is a directory and contains a system.md file
        if subdir.is_dir() and system_md_path.exists():
            # Read the contents of system.md
            system_content = system_md_path.read_text()

            # Define the output YAML file path
            yaml_file_path = templates_dir / f'{subdir.name}.yaml'

            # Create the YAML content
            yaml_content = {'system': system_content}

            # Write the content to the YAML file
            with yaml_file_path.open('w') as yaml_file:
                yaml.safe_dump(yaml_content, yaml_file, default_flow_style=False)

            print(f'Created {yaml_file_path}')


def get_latest_release():
    url = 'https://api.github.com/repos/danielmiessler/fabric/releases/latest'
    response = httpx.get(url)
    response.raise_for_status()
    return response.json()['tag_name']


def download_latest_release():
    latest_release = get_latest_release()
    url = f'https://github.com/danielmiessler/fabric/archive/{latest_release}.zip'
    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()
    zip_file_path = 'fabric.zip'
    # extract only the patterns directory
    with open(zip_file_path, 'wb') as zip_file:
        zip_file.write(response.content)
    print(f'Downloaded {zip_file_path}')
    return zip_file_path


def extract_patterns(zip_file_path, latest_release):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        latest_release_version = latest_release.split('v')[-1]
        patterns_namelist = [
            name
            for name in zip_ref.namelist()
            if name.startswith(f'fabric-{latest_release_version}/patterns/')
            and name.endswith('system.md')
        ]
        zip_ref.extractall('fabric', patterns_namelist)

        return Path('fabric') / f'fabric-{latest_release_version}' / 'patterns'


def main():
    latest_release = get_latest_release()
    zip_file_path = download_latest_release()
    base_dir = extract_patterns(zip_file_path, latest_release)
    write_llm_templates(base_dir)


if __name__ == '__main__':
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)
    main()
