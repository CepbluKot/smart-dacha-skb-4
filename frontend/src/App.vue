<template>
  <v-app>
    <v-system-bar app>
      <span
        style="text-overflow: ellipsis; overflow: hidden; white-space: nowrap"
      >
        Настройка индивидуального устройства
      </span>
      <v-spacer></v-spacer>
      <nobr>
        <span v-if="deviceConnectionStatus">
          <v-icon dense>mdi-usb</v-icon>{{ deviceConnectionPort }}
        </span>
        &nbsp;&nbsp;
        <span v-if="deviceConnectionStatus">
          <v-icon dense>mdi-checkbox-marked-circle-outline</v-icon>Подключен
        </span>
        <span v-else>
          <v-icon dense>mdi-close-circle-outline</v-icon>Отключен
        </span>
      </nobr>
    </v-system-bar>

    <v-main>
      <v-progress-linear
        v-if="!app.started"
        indeterminate
        color="indigo"
      ></v-progress-linear>

      <div v-if="!serverConnectionStatus && app.started">
        <v-container>
          <v-alert
            dense
            border="left"
            colored-border
            type="error"
            elevation="2"
          >
            Ошибка. Сервер недоступен либо выключен.
          </v-alert>
        </v-container>
      </div>

      <div v-if="serverConnectionStatus && app.started">
        <v-container fluid>
          <transition name="slide-fade">
            <v-alert
              v-if="no_comDevice"
              dense
              border="left"
              colored-border
              type="warning"
              elevation="2"
            >
              Нет доступных устройств
            </v-alert>
          </transition>
          <transition name="slide-fade">
            <v-form v-if="!deviceConnectionStatus">
              <v-row>
                <v-col cols="12" md="6" style="max-height: 65px">
                  <v-select
                    dense
                    outlined
                    :rules="formRules.comDevice"
                    label="Устройство"
                    item-text="name"
                    item-value="port"
                    v-model="input_comDevice"
                    :items="comData.com_devices"
                    :disabled="no_comDevice"
                  ></v-select>
                </v-col>

                <v-col cols="12" md="2" style="max-height: 65px">
                  <v-select
                    :items="Object.values(comData.com_speed)"
                    label="Скорость"
                    outlined
                    dense
                    v-model="input_comSpeed"
                    :disabled="no_comDevice"
                  ></v-select>
                </v-col>

                <v-col cols="12" md="2" style="max-height: 60px">
                  <v-btn
                    outlined
                    color="indigo"
                    dense
                    v-on:click="connectComDevice()"
                    :disabled="
                      no_comDevice ||
                      tryingConnectComDevice ||
                      tryingDisconnectComDevice ||
                      input_comDevice == '' ||
                      input_comSpeed == ''
                    "
                    :loading="tryingConnectComDevice"
                  >
                    Подключиться
                  </v-btn>
                </v-col>
              </v-row>
            </v-form>
            <v-form v-if="deviceConnectionStatus">
              <div class="d-flex justify-space-between">
                <div style="overflow: hidden; text-overflow: ellipsis">
                  <!--{{ deviceConnectionPort }}-->
                </div>
                <v-btn
                  outlined
                  color="red"
                  dense
                  v-on:click="disconnectComDevice()"
                  :disabled="no_comDevice"
                  :loading="tryingDisconnectComDevice"
                >
                  Отключиться
                </v-btn>
              </div>
            </v-form>
          </transition>

          <transition name="slide-fade">
            <v-content>
              <v-card
                style="
                  margin-bottom: 10px;
                  height: 200px;
                  overflow: scroll;
                  overflow-x: hidden;
                  font-family: monospace;
                  color: black;
                "
                id="terminal-window"
              >
                <v-card-text
                  :disabled="
                    no_comDevice ||
                    !deviceConnectionStatus ||
                    tryingConnectComDevice ||
                    tryingDisconnectComDevice
                  "
                >
                  <div v-for="line in resp.chat" :key="line">
                    <span v-if="line.author == 'user'" style="color: green">
                      $~
                    </span>
                    <span
                      v-else-if="line.author == 'device'"
                      style="color: blue"
                    >
                      ->
                    </span>
                    {{ line.message }}
                    <br />
                  </div>
                </v-card-text>
              </v-card>

              <v-form>
                <v-row no-gutters>
                  <v-col>
                    <v-text-field
                      prefix="~$"
                      solo
                      style="font-family: monospace"
                      :append-icon="'mdi-send'"
                      @click:append="sendComCommand(input_comCommand)"
                      :disabled="
                        no_comDevice ||
                        !deviceConnectionStatus ||
                        tryingConnectComDevice ||
                        tryingDisconnectComDevice
                      "
                      v-model="input_comCommand"
                    ></v-text-field>
                  </v-col>
                </v-row>
              </v-form>

              <v-btn
                style="display: block; margin-right: 0; margin-left: auto"
                class="mb-5"
                @click="clearButtons()"
                outlined
                color="red"
                :disabled="
                  no_comDevice ||
                  !deviceConnectionStatus ||
                  tryingConnectComDevice ||
                  tryingDisconnectComDevice ||
                  input_comCommand == ''
                "
              >
                Очистить
              </v-btn>

              <v-row>
                <div v-for="i in 9" :key="i">
                  <v-col style="min-width: 200px; width: 11vw">
                    <v-card dense>
                      <div class="text-center text-h6">{{ i }}</div>
                      <v-select
                        label="Действие"
                        item-text="caption"
                        item-value="id"
                        v-model="buttons[i]"
                        :items="SKB_device.actions"
                        outlined
                        dense
                        class="pa-2"
                        @change="changeSend()"
                        :disabled="
                          no_comDevice ||
                          !deviceConnectionStatus ||
                          tryingConnectComDevice ||
                          tryingDisconnectComDevice
                        "
                      ></v-select>
                    </v-card>
                  </v-col>
                </div>
              </v-row>
            </v-content>
          </transition>
        </v-container>
      </div>
    </v-main>
  </v-app>
</template>

<script>
import axios from "axios";

export default {
  name: "App",

  components: {},

  data: () => ({
    app: {
      started: false,
      isSendingCommand: false,
    },

    SKB_device: {
      actions: [
        { id: "1", caption: "Свет вкл." },
        { id: "2", caption: "Свет выкл." },
        { id: "3", caption: "Отопление вкл." },
        { id: "4", caption: "Отопление выкл." },
        { id: "5", caption: "Газ вкл." },
        { id: "6", caption: "Газ выкл." },
        { id: "7", caption: "Вода вкл." },
        { id: "8", caption: "Вода выкл." },
      ],
    },

    buttons: {},

    resp: "",

    comData: [],

    input_comDevice: "",
    input_comSpeed: 9600,
    no_comDevice: false,
    serverConnectionStatus: false,
    deviceConnectionStatus: false,
    deviceConnectionPort: "",
    port: "",
    tryingConnectComDevice: false,
    tryingDisconnectComDevice: false,

    input_comCommand: "",

    serverUrl: "http://127.0.0.1:5000",

    formRules: {
      comDevice: [(v) => !!v || "Выберите устройство"],
      comSpeed: [(v) => !!v || "Выберите скорость"],
    },
  }),

  methods: {
    changeSend() {
      this.input_comCommand = "";
      for (let i = 1; i <= 9; i++) {
        if (this.buttons[i] != undefined)
          this.input_comCommand +=
            "butt " + i + " actn " + this.buttons[i] + " cl rs ";
      }
    },

    clearButtons() {
      this.input_comCommand = "";
      this.buttons = {};
    },

    checkConnection() {
      axios
        .get(this.serverUrl + "/check", { timeout: 5000 })
        .then((res) => {
          if (res.data.server_working == "true") {
            this.serverConnectionStatus = true;
            this.app.started = true;

            if (res.data.device_connected == "true") {
              this.deviceConnectionStatus = true;
              this.deviceConnectionPort = res.data.device_port;
            } else this.deviceConnectionStatus = false;
          }
        })
        .catch((error) => {
          this.serverConnectionStatus = false;
          this.app.started = true;
          console.error(error);
        });
    },

    getComDevices() {
      if (!this.deviceConnectionStatus) {
        axios
          .get(this.serverUrl + "/com/show")
          .then((res) => {
            this.comData = res.data;

            if (Object.keys(res.data.com_devices).length === 0) {
              this.no_comDevice = true;
            } else {
              this.no_comDevice = false;
            }
          })
          .catch((error) => {
            console.error(error);
          });
      }
    },

    connectComDevice() {
      this.tryingConnectComDevice = true;

      const headers = {
        "Content-Type": "application/json",
      };

      axios
        .post(
          this.serverUrl + "/com/connect",
          {
            port: this.input_comDevice,
            speed: this.input_comSpeed,
          },
          {
            headers: headers,
          }
        )
        .then((response) => {
          console.log(response.data);
          this.resp = response.data;

          response.data.reply == "success"
            ? (this.deviceConnectionStatus = true)
            : (this.deviceConnectionStatus = false);
        })
        .catch((error) => {
          console.log(error);
        })
        .finally(() => {
          this.tryingConnectComDevice = false;
        });
    },

    disconnectComDevice() {
      this.tryingDisconnectComDevice = true;

      const headers = {
        "Content-Type": "application/json",
      };

      axios
        .post(
          this.serverUrl + "/com/disconnect",
          {
            command: "disconnect",
          },
          {
            headers: headers,
          }
        )
        .then((response) => {
          console.log(response.data);
          //this.resp = response.data;
          console.log("Error at disconnect");
          response.data.reply == "success"
            ? (this.deviceConnectionStatus = false)
            : (this.deviceConnectionStatus = true);
          this.resp = [];
        })
        .catch((error) => {
          console.log(error);
        })
        .finally(() => {
          this.tryingDisconnectComDevice = false;
          this.checkConnection();
        });
    },

    sendComCommand() {
      if (this.input_comCommand != "") {
        this.app.isSendingCommand = true;

        const headers = {
          "Content-Type": "application/json",
        };

        axios
          .post(
            this.serverUrl + "/com/send",
            {
              command: this.input_comCommand,
            },
            {
              headers: headers,
            }
          )
          .then((response) => {
            console.log(response.data);
            this.resp = response.data;
          })
          .catch((error) => {
            console.log(error);
          })
          .finally(() => {
            let terminalWindow = this.$el.querySelector("#terminal-window");
            terminalWindow.scrollTop = terminalWindow.scrollHeight;

            this.app.isSendingCommand = false;
          });
      }
    },
  },

  mounted() {
    this.checkConnection();
    this.getComDevices();

    setInterval(
      function () {
        if (!this.app.isSendingCommand) this.checkConnection();
      }.bind(this),
      2000
    );

    setInterval(
      function () {
        this.getComDevices();
      }.bind(this),
      2000
    );
  },
};
</script>
<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to /* .fade-leave-active до версии 2.1.8 */ {
  opacity: 0;
}

.slide-fade-enter-active {
  transition: all 0.1s ease;
}
.slide-fade-leave-active {
  transition: all 0.1s ease;
}
.slide-fade-enter, .slide-fade-leave-to
/* .slide-fade-leave-active до версии 2.1.8 */ {
  transform: translateY(-10px);
  opacity: 0;
}
</style>