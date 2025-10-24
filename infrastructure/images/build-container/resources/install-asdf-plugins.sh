set -e

pluginFile=".tool-versions"
echo "Installing asdf plugins from ${pluginFile}..."

grep ^[a-z] ${pluginFile} | while read -r plugin; do 
    echo ${plugin}
    name=${plugin%% *}
    version=${plugin#* }

    asdf plugin add ${name}
    asdf install ${name} ${version}
done

echo "Done!"