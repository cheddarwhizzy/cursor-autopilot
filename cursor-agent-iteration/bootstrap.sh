#!/usr/bin/env bash
# Cursor Agent Iteration System - Bootstrap Script
# Usage: curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Bootstrap Cursor Agent Iteration System${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository. Please run this script from your project root.${NC}"
    exit 1
fi

# Ensure cursor-agent is installed
if ! command -v cursor-agent >/dev/null 2>&1; then
  echo -e "${YELLOW}📦 Installing cursor-agent...${NC}"
  curl https://cursor.com/install -fsS | bash
  echo -e "${YELLOW}Note: You may need to add ~/.local/bin to PATH and restart your shell${NC}"
  export PATH="$HOME/.local/bin:$PATH"
fi

# Create necessary directories
echo -e "${CYAN}📁 Creating directory structure...${NC}"
mkdir -p prompts
mkdir -p scripts
mkdir -p templates

# Function to fetch template files from main branch
fetch_template_file() {
    local template_name="$1"
    local local_path="templates/${template_name}.template"
    local remote_url="https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/templates/${template_name}.template"
    
    echo -e "${CYAN}📥 Fetching ${template_name}.template from main branch...${NC}"
    
    if curl -fsSL "$remote_url" -o "$local_path"; then
        echo -e "${GREEN}✅ Downloaded ${template_name}.template${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to download ${template_name}.template from main branch${NC}"
        echo -e "${YELLOW}⚠️  This may indicate the template file doesn't exist in the main branch yet${NC}"
        return 1
    fi
}

# Function to fetch prompt files from main branch
fetch_prompt_file() {
    local prompt_name="$1"
    local local_path="prompts/${prompt_name}.md"
    local remote_url="https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/prompts/${prompt_name}.md"
    
    echo -e "${CYAN}📥 Fetching ${prompt_name}.md from main branch...${NC}"
    
    if curl -fsSL "$remote_url" -o "$local_path"; then
        echo -e "${GREEN}✅ Downloaded ${prompt_name}.md${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to download ${prompt_name}.md from main branch${NC}"
        echo -e "${YELLOW}⚠️  This may indicate the prompt file doesn't exist in the main branch yet${NC}"
        return 1
    fi
}

# Function to create script from template
create_script_from_template() {
    local template_name="$1"
    local script_name="$2"
    local template_path="templates/${template_name}.template"
    local script_path="scripts/${script_name}"
    
    if [[ -f "$template_path" ]]; then
        echo -e "${CYAN}📝 Creating ${script_name} from template...${NC}"
        cp "$template_path" "$script_path"
        chmod +x "$script_path"
        echo -e "${GREEN}✅ Created ${script_name}${NC}"
    else
        echo -e "${RED}❌ Template ${template_name}.template not found${NC}"
        return 1
    fi
}

# Fetch all template files from main branch
echo -e "${CYAN}📥 Fetching template files from main branch...${NC}"

TEMPLATE_FILES=(
    "init-iterate.sh"
    "check-complete.sh" 
    "iterate-loop.sh"
    "add-feature.sh"
    "archive-completed.sh"
    "Makefile"
    "CURSOR_ITERATION_README.md"
)

for template in "${TEMPLATE_FILES[@]}"; do
    if ! fetch_template_file "$template"; then
        echo -e "${YELLOW}⚠️  Using local template for ${template}${NC}"
    fi
done

# Fetch prompt files from main branch
echo -e "${CYAN}📥 Fetching prompt files from main branch...${NC}"

PROMPT_FILES=(
    "initialize-iteration-universal"
    "add-feature"
)

for prompt in "${PROMPT_FILES[@]}"; do
    if ! fetch_prompt_file "$prompt"; then
        echo -e "${YELLOW}⚠️  Using fallback prompt for ${prompt}${NC}"
        # Create fallback prompts if remote fetch fails
        case "$prompt" in
            "initialize-iteration-universal")
                echo -e "${CYAN}📝 Using fallback template for initialize-iteration-universal...${NC}"
                cp templates/fallback-initialize-iteration-universal.md.template prompts/initialize-iteration-universal.md
                ;;
            "add-feature")
                echo -e "${CYAN}📝 Using fallback template for add-feature...${NC}"
                cp templates/fallback-add-feature.md.template prompts/add-feature.md
                ;;
        esac
    fi
done

# Create scripts from templates
echo -e "${CYAN}📝 Creating scripts from templates...${NC}"

create_script_from_template "init-iterate.sh" "init-iterate.sh"
create_script_from_template "check-complete.sh" "check-complete.sh"
create_script_from_template "iterate-loop.sh" "iterate-loop.sh"
create_script_from_template "add-feature.sh" "add-feature.sh"
create_script_from_template "archive-completed.sh" "archive-completed.sh"

# Handle Makefile creation/update
echo -e "${CYAN}📝 Creating/updating Makefile...${NC}"

if [[ ! -f "Makefile" ]]; then
    echo -e "${YELLOW}📝 Creating new Makefile...${NC}"
    cp templates/Makefile.template Makefile
    echo -e "${GREEN}✅ Created Makefile${NC}"
else
    echo -e "${CYAN}📝 Updating existing Makefile with cursor-agent-iteration targets...${NC}"
    
    # Define all cursor-agent-iteration targets
    CURSOR_TARGETS=("iterate-init" "iterate" "iterate-complete" "iterate-loop" "add-feature" "archive-completed" "task-status")
    
    # Check if any cursor-agent-iteration targets exist
    CURSOR_TARGETS_EXIST=false
    for target in "${CURSOR_TARGETS[@]}"; do
        if grep -q "## $target:" Makefile; then
            CURSOR_TARGETS_EXIST=true
            break
        fi
    done
    
    if [[ "$CURSOR_TARGETS_EXIST" == "true" ]]; then
        echo -e "${YELLOW}🔄 Found existing cursor-agent-iteration targets${NC}"
        echo -e "${CYAN}📝 Removing old targets and adding fresh ones...${NC}"
        
        # Create a backup
        cp Makefile Makefile.backup
        echo -e "${CYAN}📁 Created backup: Makefile.backup${NC}"
        
        # Find the first cursor target line and remove everything from there to the end
        FIRST_CURSOR_LINE=$(grep -n "^## iterate-init:" Makefile | head -1 | cut -d: -f1)
        
        if [[ -n "$FIRST_CURSOR_LINE" ]]; then
            echo -e "${CYAN}🗑️  Found cursor targets starting at line $FIRST_CURSOR_LINE${NC}"
            
            # Remove everything from the first cursor target to the end
            head -n $((FIRST_CURSOR_LINE - 1)) Makefile > Makefile.temp
            mv Makefile.temp Makefile
            
            echo -e "${GREEN}✅ Removed cursor targets from line $FIRST_CURSOR_LINE onwards${NC}"
        else
            echo -e "${CYAN}ℹ️  No existing cursor targets found${NC}"
        fi
        
        echo -e "${GREEN}✅ Removed old cursor-agent-iteration targets${NC}"
    else
        echo -e "${CYAN}📝 No existing cursor-agent-iteration targets found${NC}"
    fi
    
    # Add fresh cursor-agent-iteration targets
    echo -e "${CYAN}📝 Adding fresh cursor-agent-iteration targets...${NC}"
    cat templates/Makefile.template >> Makefile
    echo -e "${GREEN}✅ Added fresh cursor-agent-iteration targets to Makefile${NC}"
fi

# Create README from template
echo -e "${CYAN}📝 Creating README from template...${NC}"
cp templates/CURSOR_ITERATION_README.md.template CURSOR_ITERATION_README.md
echo -e "${GREEN}✅ Created CURSOR_ITERATION_README.md${NC}"

# Note: Control files (architecture.md, decisions.md, test_plan.md, etc.) are created
# by 'make iterate-init' with project-specific analysis, not by bootstrap.sh
echo -e "${CYAN}📋 Control files are managed by 'make iterate-init' - preserving existing project analysis${NC}"

echo ""
echo -e "${GREEN}✅ Bootstrap complete!${NC}"
echo ""
echo -e "${CYAN}📋 Created Files:${NC}"
echo -e "   - ${YELLOW}prompts/initialize-iteration-universal.md${NC} - Universal initialization prompt (fetched from main branch)"
echo -e "   - ${YELLOW}prompts/add-feature.md${NC} - Feature addition prompt (fetched from main branch)"
echo -e "   - ${YELLOW}scripts/init-iterate.sh${NC} - Initialization script"
echo -e "   - ${YELLOW}scripts/check-complete.sh${NC} - Completion checker"
echo -e "   - ${YELLOW}scripts/iterate-loop.sh${NC} - Continuous loop script"
echo -e "   - ${YELLOW}scripts/add-feature.sh${NC} - Feature addition script"
echo -e "   - ${YELLOW}scripts/archive-completed.sh${NC} - Task archiving script"
echo -e "   - ${YELLOW}Makefile${NC} - Updated with cursor-agent-iteration targets"
echo -e "   - ${YELLOW}CURSOR_ITERATION_README.md${NC} - Complete documentation"
echo ""
echo -e "${CYAN}📋 Control Files (created by 'make iterate-init'):${NC}"
echo -e "   - ${YELLOW}architecture.md${NC} - Architecture documentation"
echo -e "   - ${YELLOW}progress.md${NC} - Progress tracking"
echo -e "   - ${YELLOW}decisions.md${NC} - Architectural Decision Records"
echo -e "   - ${YELLOW}test_plan.md${NC} - Test coverage plans"
echo -e "   - ${YELLOW}qa_checklist.md${NC} - Quality assurance checklist"
echo -e "   - ${YELLOW}CHANGELOG.md${NC} - Conventional commits log"
echo -e "   - ${YELLOW}context.md${NC} - Project context"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo -e "   ${YELLOW}make help${NC}              # Show all available commands"
echo -e "   ${YELLOW}make iterate-init${NC}      # Initialize and analyze your repository"
echo -e "   ${YELLOW}make add-feature${NC}       # Add new feature/requirements (analyzes codebase first)"
echo -e "   ${YELLOW}make task-status${NC}       # Show current task status and progress"
echo -e "   ${YELLOW}make iterate${NC}           # Run the next task in the backlog"
echo -e "   ${YELLOW}make iterate-loop${NC}      # Run iterations until all tasks complete"
echo -e "   ${YELLOW}make iterate-complete${NC}  # Check if all tasks are completed"
echo -e "   ${YELLOW}make archive-completed${NC} # Archive completed tasks"
echo ""
echo -e "${CYAN}📚 Documentation:${NC}"
echo -e "   - Read ${YELLOW}CURSOR_ITERATION_README.md${NC} for detailed usage"
echo -e "   - Check ${YELLOW}prompts/iterate.md${NC} after initialization"
echo -e "   - Review ${YELLOW}tasks.md${NC} for your technology-specific task backlog"
echo ""
echo -e "${GREEN}🎉 Happy iterating!${NC}"