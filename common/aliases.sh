# { Part of bashrc file [ scripts/common/aliases.sh ]

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias watch='watch -n 0.1 --color'
alias ka='killall -9'
alias kp='kill -9'
alias etail='tail -fn+1'
alias tmux='TERM=xterm-256color tmux'
alias please='sudo'
alias vim_clsw="find . -type f -name '*.sw*' -delete"
command -v nvim &>/dev/null && alias vim='nvim'

if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias dir='dir --color=auto'
    alias vdir='vdir --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

function br_import() {
    # shellcheck disable=1090
    source "${DOTTOOLS_LIB_PATH}/${1}.sh"
}

# } Part of bashrc file [ scripts/common/aliases.sh ]
