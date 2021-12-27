import { lovelace_view, load_lovelace, lovelace, hass } from "card-tools/src/hass";
import { popUp, closePopUp } from "card-tools/src/popup";
import { fireEvent } from "card-tools/src/event";
import {
  applyThemesOnElement,
  getLovelace
} from 'custom-card-helpers';

window.mobileAndTabletCheck = function() {
  let check = false;
  (function(a){if(/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino|android|ipad|playbook|silk/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))) check = true;})(navigator.userAgent||navigator.vendor||window.opera);
  return check;
};

class DwainsDashboard {

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  async _getConfig() {
    let lovelace_load;
    while(!lovelace_load) {
      lovelace_load = getLovelace();
      if(!lovelace_load) {
        await this.sleep(500);
      }
    }
    this.lovelace_load = getLovelace();
    this.frontend_stuff();
  }

  _connect() {
    if(!window.hassConnection) {
      window.setTimeout(() => this._connect(), 100);
    } else {
      window.hassConnection.then((conn) => this.connect(conn.conn));
    }
  }

  constructor() {
    this.cast = document.querySelector("hc-main") !== null;
    if(!this.cast) {
      this._connect();
      document.querySelector("home-assistant").addEventListener("hass-more-info", this.popup_card.bind(this));
    } else {
      this.connect(hass().connection);
    }

    window.setTimeout(this._getConfig.bind(this), 500);

    const updater = this.update.bind(this);
    window.addEventListener("location-changed", updater);
    window.addEventListener("popstate", updater);

    let link = document.createElement('link');
    link.rel = 'stylesheet';
    link.type = 'text/css';
    link.href = 'https://fonts.googleapis.com/css?family=Open+Sans&display=swap';
    link.media = 'all';
    document.getElementsByTagName('head')[0].appendChild(link);

    const pjson = require('../package.json');
    console.info(
      `%c  DWAINS_DASHBOARD JS  \n%c    Version ${pjson.version}     `,
      "color: #2fbae5; font-weight: bold; background: black",
      "color: white; font-weight: bold; background: dimgray"
    );
  }

  update(){
    let path = window.location.pathname;
    let nav_path = path.substring(1, path.lastIndexOf('/'));

    //Location has changed check if user is still in dwains dashboard
    if(nav_path == "dwains-dashboard"){
      this.frontend_stuff();
    }
  }

  getRoot() {
    let root = document.querySelector('home-assistant');
    root = root && root.shadowRoot;
    root = root && root.querySelector('home-assistant-main');
    root = root && root.shadowRoot;
    root = root && root.querySelector('app-drawer-layout partial-panel-resolver');
    root = root && root.shadowRoot || root;
    root = root && root.querySelector('ha-panel-lovelace');
    root = root && root.shadowRoot;
    root = root && root.querySelector('hui-root');
    return root;
  }

  frontend_stuff(){
    let lovelace = getLovelace();
    //console.info(lovelace);
    if(lovelace){
      if(lovelace.config){
        //console.log(lovelace.config.dwains_dashboard);
        if(lovelace.config.dwains_dashboard) {
          this.custom_header(lovelace.config.dwains_dashboard);
          this.set_theme(lovelace.config.dwains_dashboard);

          //console.log(lovelace.config.dwains_dashboard);
        }
      }
    }
  }

  custom_header(config){
    const root = this.getRoot();

    if(!root.getAttribute("data-dwains-dashboard-header")){
      //console.log('Start the custom header')

      root.setAttribute("data-dwains-dashboard-header", true);

      //Hide prev/next buttons
      root.shadowRoot.querySelector('app-header').querySelector('app-toolbar').querySelector('ha-tabs').shadowRoot.querySelectorAll('paper-icon-button').forEach(el => {
        el.style.display = 'none';
      });

      //Check if mobile or tablet, if yes put nav as footer
      if(window.mobileAndTabletCheck()){
        root.shadowRoot.querySelector('#view').style.cssText = 'margin-top: -64px;';
        root.shadowRoot.querySelector('app-header').style.cssText = 'top: auto; bottom: 0px;';

        //Hide menu button
        root.shadowRoot.querySelector('app-header').querySelector('app-toolbar').querySelector('ha-button-menu').style.display = 'none';  
      } 
    }
  }

  set_theme(config){
    const root = this.getRoot();

    console.log('set_theme');

    if(!root.getAttribute("data-dwains-dashboard-theme")){
      root.setAttribute("data-dwains-dashboard-theme", true);

      //See if user has set default HA theme or Dwains Theme handling
      if(config.theme !== "HA selected theme"){
        let sunState = "";
        if(hass().states["sun.sun"]){
          sunState = hass().states["sun.sun"].state;
        } else {
          console.log('sun.sun not available!');
        }
        const themes = {themes: JSON.parse(config.themes.replace(/placeholder_primary_color/g, config.primary_color))}
        let theme = "dwains-theme-light";

        switch(config.theme) {
          case "Auto Mode (Dark/Light)":
            if(sunState == "above_horizon"){
              theme = "dwains-theme-light"
            } else {
              theme = "dwains-theme-dark"
            }
            break;
          case "Auto Mode (Black/White)":
            if(sunState == "above_horizon"){
              theme = "dwains-theme-white"
            } else {
              theme = "dwains-theme-black"
            }
            break;
          case "Dark Mode":
            theme = "dwains-theme-dark"
            break;
          case "Light Mode":
            theme = "dwains-theme-light"
            break;
          case "Black Mode":
            theme = "dwains-theme-black"
            break;
          case "White Mode":
            theme = "dwains-theme-white"
            break;
          default:
            theme = "dwains-theme-light"
            break;
        }

        applyThemesOnElement(root, themes, theme, true);

      }
    }

  }

  connect(conn) {
    this.conn = conn
    conn.subscribeEvents(() => this._reload(), "dwains_dashboard_reload");
  }

  _reload() {
    const ll = lovelace_view();
    if (ll)
      fireEvent("config-refresh", {}, ll);
      let path = window.location.pathname;
      let nav_path = path.substring(1, path.lastIndexOf('/'));

      //Location check if user is in dwains dashboard
      //if(nav_path == "dwains-dashboard"){
        setTimeout(function() {
          document.location.reload()
        }, 1000);
      //}
  }

  popup_card(ev) {
    if(!lovelace()) return;
    const ll = lovelace();
    const data = {
      ...ll.config.dwains_dashboard.popup_cards,
    };
    if(!ev.detail || !ev.detail.entityId) return;

    //Make an array with custom popups set by user
    const d = data[ev.detail.entityId];
    let cardData;
    let cardTitle;
    let customCard = false;

    if(!d || 0 === d.length) {
      //Entity doesn't have a custom popup, let's check if it needs a global popup
      const domain = ev.detail.entityId.split(".")[0];
      let popupData;

      if(popupData = ll.config.dwains_dashboard[domain+'_popup']){
        cardData = JSON.parse(JSON.stringify(popupData.card).replace(/domain.placeholder/g, ev.detail.entityId));
        cardTitle = hass().states[ev.detail.entityId].attributes.friendly_name;
        customCard = true;
      }
    } else {
      cardData = d.card;
      cardTitle = d.title !== null ? d.title : "";
      customCard = true;
    }

    if(customCard === true){
      window.setTimeout(() => {
        fireEvent("hass-more-info", {entityId: "."}, document.querySelector("home-assistant"));
        popUp(cardTitle, cardData, false, '');
      }, 50);
    } else {
      return;
    }
  }
  
}


const bases = [customElements.whenDefined('hui-masonry-view'), customElements.whenDefined('hc-lovelace')];
Promise.race(bases).then(() => {
  window.dwains_dashboard = window.dwains_dashboard || new DwainsDashboard();

  const LitElement = customElements.get('hui-masonry-view')
    ? Object.getPrototypeOf(customElements.get('hui-masonry-view'))
    : Object.getPrototypeOf(customElements.get('hc-lovelace'));

  const html = LitElement.prototype.html;

  const css = LitElement.prototype.css;


  class DwainsDashboardLayout extends LitElement {
    setConfig(_config) {}

    static get properties() {
      return {
        cards: {type: Array, attribute: false}
      };
    }

    lovelace() {
      var root = document.querySelector("hc-main");
      if(root) {
        var ll = root._lovelaceConfig;
        ll.current_view = root._lovelacePath;
        return ll;
      }
    
      root = document.querySelector("home-assistant");
      root = root && root.shadowRoot;
      root = root && root.querySelector("home-assistant-main");
      root = root && root.shadowRoot;
      root = root && root.querySelector("app-drawer-layout partial-panel-resolver");
      root = root && root.shadowRoot || root;
      root = root && root.querySelector("ha-panel-lovelace")
      root = root && root.shadowRoot;
      root = root && root.querySelector("hui-root")
      if (root) {
        var ll =  root.lovelace
        ll.current_view = root.___curView;
        return ll;
      }
    
      return null;
    }

    static get styles() {
      return [
        css`
        #dwains_dashboard {
          max-width: 1465px;
          padding-bottom: 50px;
          margin: 0 auto;
          font-family: "Open Sans", sans-serif !important;
        }
        ha-fab {
          font-size: 18px;
          border: 2px solid #4591B8;
          padding: 5px;
          margin-bottom: 50px;
        }
        `
      ]
    }

    clicked() {
      if(lovelace().mode !== "yaml") return;
      lovelace().setEditMode(!lovelace().editMode);
      this.requestUpdate();
    }

    _addCard() {
      console.log('test');
      //fireEvent(this, "ll-create-card");
      this.dispatchEvent(new CustomEvent("ll-create-card"));
    }

    async updated(){
      //console.log('updated');
    }

    render() {
      if(!this.cards) {
        return html``;
      }
      return html`
        <div id="dwains_dashboard">
          ${this.cards.map((card) => html`${card}`)}
          
        </div>
      `;
    }
  }
  if (!customElements.get("dwains-dashboard")) {
    customElements.define("dwains-dashboard", DwainsDashboardLayout);
  }
});