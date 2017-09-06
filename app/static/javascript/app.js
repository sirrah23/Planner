const getPlannerLinkWindow = () => {
    return window.location.href.split(/\//).pop();
}

const plannerApiConn = {
    get(link, cb){
        axios.get("/api/v1/planner/"+link)
        .then(function(response){
             if(cb){
                 cb(response.data);
            }
        });
    },
    /*
    patch(link, data){
        axios.patch("/api/v1/planner/"+link, {data});
    }
    */
}

const itemApiConn = {
  post(link, data){
    return axios.post("/api/v1/planner/"+link+"/item", {data});
  },
  delete(link, _id){
    return axios.delete("/api/v1/planner/"+link+"/item/"+_id);
  },
  patch(link, _id, data){
    console.log(`Attempting to patch item ${_id} on ${link} with ${data}`);
    return axios.patch("/api/v1/planner/"+link+"/item/"+_id, {data});
  }
}

const groupApiConn = {
  post(link, data){
    return axios.post("/api/v1/planner/"+link+"/group", {data});
  },
  delete(link, _id){
    return axios.delete("/api/v1/planner/"+link+"/group/"+_id);
  }
}

const initGroupItem = (item) => {
    const defaults = {
        moved_to: "",
        checked: false,
        expanded: false,
        deleted: false,
    }
    return Object.assign({}, defaults, item);
}

const initGroupItems = (groups) => {
    const initialized_groups = {};
    for (let g in groups){
      initialized_groups[g] = { _id: groups[g]._id, items:groups[g].items.map( (i) => { return initGroupItem(i); } ) };
    }
    return initialized_groups;
}

//FIXME: Get rid of this way of sending updates...
const cleanGroupItem = (item) =>{
    ({name, checked} = item);
    return {name, checked};
}

const cleanGroupItems = (groups) => {
    const cleaned_groups = {};
    for (let g in groups){
        cleaned_groups[g] = groups[g].map( (i) => { return cleanGroupItem(i); } );
    }
    return cleaned_groups;
}

const app = new Vue({
   el: "#planner",
   data: {
      item: "",
      items : [],
      group: "",
      groups: {}
   },
   created: function(){
       const me = this;
       //TODO: Inject the api conn...
       plannerApiConn.get(
               getPlannerLinkWindow(),
               (respData) => {
                   me.items = respData.items;
                   me.groups = initGroupItems(respData.groups);
               });
   },
   methods: {
      add_new_item : function(event){
          if(this.item.length == 0)
              return;
          itemApiConn.post(getPlannerLinkWindow(), JSON.stringify({name: this.item}))
            .then( (new_item) => { app.items.push(new_item.data); } );
          this.item = "";
      },
      add_new_group: function(event){
          if(this.group.length == 0)
              return;
          //FIXME: Group passed in that already exists...
          groupApiConn.post(getPlannerLinkWindow(), JSON.stringify({name: this.group}))
              .then((posted_group_data) =>{
                  app.groups[app.group] = {};
                  app.groups[app.group]._id = posted_group_data.data._id;
                  app.groups[app.group].items = [];
                  app.group = "";
              });
      },
      shuffle_items: function(event){
          /*
          / TODO: The algorithm should not always
          / start at the first group because if the
          / user repeatedly adds on item and shuffles
          / then the first user will get that object every
          / time.
         */
          const all_groups = Object.keys(this.groups);
          const num_groups = all_groups.length;
          if(num_groups == 0)
              return;
          let curr_item, rand_idx, curr_group_idx = 0;
          while(this.items.length > 0){
              rand_idx = Math.floor(Math.random() * this.items.length);
              //TODO: Create a function to generate this object
              curr_item = initGroupItem(this.items.splice(rand_idx, 1)[0]);
              //TODO: group_name -> group_id
              this.groups[all_groups[curr_group_idx]].items.push(curr_item);
              itemApiConn.patch(getPlannerLinkWindow(), curr_item._id, JSON.stringify({group: this.groups[all_groups[curr_group_idx]]._id}));
              curr_group_idx = (curr_group_idx + 1) % num_groups;
          }
      },
      move_item: function(group_name){
          let item_to_move;
          let i;

          //Find the item that we are supposed to try and move
          for(i = 0; i < this.groups[group_name].items.length; i++){
              //FIXME: Hack until proper data communicator object is created...
              //Can't just do app.groups=... and app.items=... directly in the
              //create method; have to initialize with proper fields
              if(!["", undefined].includes(this.groups[group_name].items[i].moved_to)){
                  item_to_move = this.groups[group_name].items[i];
                  break;
              }
          }

          if(item_to_move === undefined)
              return;

          //If the item was somehow moved to a the group it is
          //already in somehow then quit.
          if(item_to_move.moved_to === group_name)
              return;

          const curr_item_id = item_to_move._id;
          const new_group = item_to_move.moved_to;
          const new_group_id = this.groups[new_group]._id;
          item_to_move.moved_to = "";

          //Finally do the actual item move
          itemApiConn.patch(getPlannerLinkWindow(), curr_item_id, JSON.stringify({group: new_group_id}))
              .then(() => {
                  //Once the group for the item is updated on the backend update it on the UI as well...
                  app.groups[new_group].items.push(item_to_move);
                  const remove_idx = app.groups[group_name].items.indexOf(item_to_move);
                  app.groups[group_name].items.splice(remove_idx,1);
                  app.$forceUpdate();
              });
      },
      checkItem: function(item){
        const item_id = item._id;
        const toggled_check = !item.checked;
        //NOTE: Do this upon next tick so the checked property gets updated first for the item
        Vue.nextTick(() =>{
          itemApiConn.patch(getPlannerLinkWindow(), item_id, JSON.stringify({checked: toggled_check}))
        });
      },
      deleteItem: function(item_id){
        for(let i = 0; i < this.items.length; i++){
            if(this.items[i]._id === item_id){
                this.items.splice(i,1);
            }
        }
        itemApiConn.delete(getPlannerLinkWindow(), item_id);
      },
      deleteItemFromGroup: function(group_name){
        //NOTE: Assumption, can only delete one item at a time...
        const items = this.groups[group_name].items;
        for(let i = items.length-1; i >= 0; i--){
            if (items[i].deleted){
                itemApiConn.delete(getPlannerLinkWindow(), items[i]._id)
                    .then(() => {
                        items.splice(i, 1);
                    });
                return;
            }
        }
      },
  },
});
