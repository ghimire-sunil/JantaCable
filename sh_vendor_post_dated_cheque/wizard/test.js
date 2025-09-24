import MainComponent from "@stock_barcode/components/main";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(MainComponent.prototype,{
setup(){
super.setup(...arguments)
this.actionService = useService("action");
}
,
_onClickAddProduct(){
const action = {
name: "Create New Product",
res_model: "product.template",
type: "ir.actions.act_window",
views: [[false, "form"]],
view_mode: "form",
target:'new'
}
return this.actionService.doAction(action)
},

_onClickPO(){
    line_list = this.env.model.currentState.lines //contains a dict
    product_ids = line_list.map(line => line['id'])
    
const action = {
name: "Create New PO",
res_model: "purchase.order",
type: "ir.actions.act_window",
views: [[false, "form"]],
view_mode: "form",
context: {
    default_order_line:[(0,0,{        
        product_id: product_ids[0],
    })
    ]
},


target:'new',
}
return this.actionService.doAction(action)
}
})