/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { MainComponentsContainer } from "@web/core/main_components_container"
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";

const { onMounted } = owl;

patch(MainComponentsContainer.prototype, "whisperchat_bits.MainComponentsContainerPatch", {
    setup() {
        this._super(...arguments);
        this.httpService = useService("http");
        const body = document.getElementsByTagName('head')[0];
        this.rpc = useService("rpc");
        onMounted(async() => {
            const chatbot = await this.rpc("/get/chatbot");
            if(chatbot) {
                const script = document.createElement("script");
                // script.id = "whisperchat-ai";
                script.type = "text/javascript";
                script.src = "https://widget.whisperchat.ai/embed.js";;
                script.id = chatbot.id;
                // // script.defer = true;
                const chatScript = document.getElementById(chatbot);
                if(chatScript && chatScript.length > 0) {
                    return;
                } else {
                    if(chatbot.front_end && chatbot.back_end) {
                        if(session.is_frontend) {
                            if(window.self !== window.top) {
                                return;
                            } else {
                                body.appendChild(script);
                            }
                        } else {
                            body.appendChild(script);
                        }
                    } else {
                        if(chatbot.front_end) {
                            if(session.is_frontend) {
                                body.appendChild(script);
                            }
                        } 
                        if(chatbot.back_end) {
                            if(!Boolean(session.is_frontend)) {
                                body.appendChild(script);
                            }
                        }
                    }
        
                }
            }
        }) 
    },
})